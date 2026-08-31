"""Tests for bulk worker account-statuses endpoint (N+1 optimization)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://slot-reserve-23.preview.emergentagent.com").rstrip("/")
TENANT_ID = "tenant_bsb_001"

ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASS = "Admin123!"
WORKER_EMAIL = "worker@salon.com"
WORKER_PASS = "Worker123!"


def _login(email, password):
    return requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=30)


def _hdr(token, tenant=True):
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if tenant:
        h["X-Tenant-ID"] = TENANT_ID
    return h


@pytest.fixture(scope="module")
def admin_token():
    r = _login(ADMIN_EMAIL, ADMIN_PASS)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def worker_auth():
    r = _login(WORKER_EMAIL, WORKER_PASS)
    assert r.status_code == 200, f"Worker login failed: {r.status_code} {r.text}"
    return r.json()


# --- Bulk endpoint: auth / RBAC ---
class TestAccountStatusesAuth:
    def test_no_auth_returns_401(self):
        r = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers={"X-Tenant-ID": TENANT_ID}, timeout=30)
        assert r.status_code in (401, 403), f"Expected 401, got {r.status_code} {r.text}"
        assert r.status_code == 401, f"Expected 401 without auth, got {r.status_code}"

    def test_worker_token_returns_403(self, worker_auth):
        r = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=_hdr(worker_auth["access_token"]), timeout=30)
        assert r.status_code == 403, f"Expected 403 for worker, got {r.status_code} {r.text}"

    def test_invalid_token_returns_401(self):
        r = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=_hdr("bogus.token.value"), timeout=30)
        assert r.status_code == 401, f"Expected 401 for bad token, got {r.status_code} {r.text}"


# --- Bulk endpoint: shape and correctness ---
class TestAccountStatusesData:
    def test_admin_returns_dict_shape(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=_hdr(admin_token), timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        data = r.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        for wid, val in data.items():
            assert isinstance(wid, str) and wid, "worker_id key must be non-empty string"
            assert set(["has_account", "email", "created_at"]).issubset(val.keys()), f"Missing keys in {val}"
            assert val["has_account"] is True
            assert isinstance(val["email"], str) and "@" in val["email"]
            assert "_id" not in val, "MongoDB _id leaked into response"

    def test_marija_account_present(self, admin_token, worker_auth):
        marija_worker_id = worker_auth.get("worker_id")
        assert marija_worker_id, "worker login did not return worker_id"
        r = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=_hdr(admin_token), timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert marija_worker_id in data, f"Marija worker_id {marija_worker_id} missing from {list(data.keys())}"
        assert data[marija_worker_id]["email"] == WORKER_EMAIL
        assert data[marija_worker_id]["has_account"] is True

    def test_bulk_matches_individual_endpoint(self, admin_token):
        """Bulk result must be consistent with per-worker GET /workers/{id}/account."""
        hdr = _hdr(admin_token)
        workers = requests.get(f"{BASE_URL}/api/workers?active_only=false", headers=hdr, timeout=30)
        assert workers.status_code == 200, workers.text
        workers = workers.json()
        assert len(workers) > 0, "No workers found in tenant"

        bulk = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=hdr, timeout=30)
        assert bulk.status_code == 200
        bulk = bulk.json()

        for w in workers:
            ind = requests.get(f"{BASE_URL}/api/workers/{w['id']}/account", headers=hdr, timeout=30)
            assert ind.status_code == 200, f"{w['id']}: {ind.status_code} {ind.text}"
            ind = ind.json()
            in_bulk = bulk.get(w["id"])
            if ind.get("has_account"):
                assert in_bulk is not None, f"Worker {w['name']} has account but missing from bulk"
                assert in_bulk["email"] == ind["email"]
            else:
                assert in_bulk is None, f"Worker {w['name']} has no account but present in bulk"

    def test_no_extraneous_worker_ids(self, admin_token):
        """Every key in bulk response should map to an existing worker in the tenant."""
        hdr = _hdr(admin_token)
        workers = requests.get(f"{BASE_URL}/api/workers?active_only=false", headers=hdr, timeout=30).json()
        worker_ids = {w["id"] for w in workers}
        bulk = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=hdr, timeout=30).json()
        orphans = [k for k in bulk if k not in worker_ids]
        assert not orphans, f"Bulk response contains worker_ids with no matching worker: {orphans}"


# --- Regression: create account / reset password still work ---
class TestAccountLifecycleRegression:
    def test_create_then_bulk_then_delete(self, admin_token):
        hdr = _hdr(admin_token)
        # create a temp worker
        cr = requests.post(f"{BASE_URL}/api/workers", headers=hdr, json={
            "name": "TEST_BulkStatusWorker", "services": [], "work_start": "09:00",
            "work_end": "17:00", "days_off": []
        }, timeout=30)
        assert cr.status_code == 200, f"worker create failed: {cr.status_code} {cr.text}"
        wid = cr.json()["id"]

        try:
            # not in bulk before account creation
            bulk = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=hdr, timeout=30).json()
            assert wid not in bulk, "New worker without account should be absent from bulk response"

            # create account
            email = "test_bulkstatus@salon.com"
            acc = requests.post(f"{BASE_URL}/api/workers/{wid}/create-account", headers=hdr,
                                json={"email": email, "language_preference": "sr"}, timeout=30)
            assert acc.status_code == 200, f"create-account failed: {acc.status_code} {acc.text}"
            body = acc.json()
            assert body.get("temp_password"), "temp_password missing"
            assert body["email"] == email

            # now present in bulk
            bulk = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=hdr, timeout=30).json()
            assert wid in bulk, "Worker with new account missing from bulk response"
            assert bulk[wid]["email"] == email
            assert bulk[wid]["has_account"] is True

            # reset password works
            rp = requests.put(f"{BASE_URL}/api/workers/{wid}/reset-password", headers=hdr, timeout=30)
            assert rp.status_code == 200, f"reset-password failed: {rp.status_code} {rp.text}"
            assert rp.json().get("temp_password")

            # delete account -> gone from bulk
            da = requests.delete(f"{BASE_URL}/api/workers/{wid}/account", headers=hdr, timeout=30)
            assert da.status_code == 200, da.text
            bulk = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=hdr, timeout=30).json()
            assert wid not in bulk, "Deleted account still present in bulk response"
        finally:
            requests.delete(f"{BASE_URL}/api/workers/{wid}/account", headers=hdr, timeout=30)
            requests.delete(f"{BASE_URL}/api/workers/{wid}", headers=hdr, timeout=30)


# --- Regression: route ordering (static path not shadowed by /{worker_id}/...) ---
class TestRouteOrdering:
    def test_account_statuses_not_treated_as_worker_id(self, admin_token):
        r = requests.get(f"{BASE_URL}/api/workers/account-statuses", headers=_hdr(admin_token), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), dict)
        assert "has_account" not in r.json(), "Response looks like single-account payload; route shadowing bug"
