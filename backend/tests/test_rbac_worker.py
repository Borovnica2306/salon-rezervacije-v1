"""RBAC worker role tests for salon booking multi-tenant PWA."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://slot-reserve-23.preview.emergentagent.com").rstrip("/")
TENANT_ID = "tenant_bsb_001"
TENANT_SLUG = "beauty-studio-bor"

WORKER_EMAIL = "worker@salon.com"
WORKER_PASS = "Worker123!"
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASS = "Admin123!"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    return r


@pytest.fixture(scope="module")
def worker_login():
    r = _login(WORKER_EMAIL, WORKER_PASS)
    assert r.status_code == 200, f"Worker login failed: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def admin_login():
    r = _login(ADMIN_EMAIL, ADMIN_PASS)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()


def _hdr(token, tenant=True):
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if tenant:
        h["X-Tenant-ID"] = TENANT_ID
    return h


# --- Worker login response tests ---
class TestWorkerLogin:
    def test_worker_login_returns_worker_role_and_id(self, worker_login):
        data = worker_login
        assert data["role"] == "worker", f"Expected role=worker, got {data.get('role')}"
        assert data.get("worker_id"), "worker_id should be present and non-empty"
        assert data.get("slug") == TENANT_SLUG, f"Expected slug={TENANT_SLUG}, got {data.get('slug')}"
        assert data.get("tenant_id") == TENANT_ID
        assert data.get("access_token")

    def test_admin_login_returns_admin_role(self, admin_login):
        data = admin_login
        assert data["role"] == "admin"
        assert data.get("slug") == TENANT_SLUG

    def test_worker_me_endpoint(self, worker_login):
        token = worker_login["access_token"]
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=_hdr(token, tenant=False))
        assert r.status_code == 200
        me = r.json()
        assert me.get("role") == "worker"
        assert me.get("worker_id"), "worker_id missing in /me"
        assert me.get("worker_id") == worker_login["worker_id"]


# --- Reservations filtering ---
class TestWorkerReservations:
    def test_worker_reservations_scoped(self, worker_login):
        token = worker_login["access_token"]
        wid = worker_login["worker_id"]
        r = requests.get(f"{BASE_URL}/api/reservations", headers=_hdr(token))
        assert r.status_code == 200, r.text
        items = r.json()
        assert isinstance(items, list)
        # Verify each reservation belongs to this worker
        for it in items:
            worker_ids = set()
            if it.get("worker_id"):
                worker_ids.add(it["worker_id"])
            for p in it.get("service_worker_pairs", []) or []:
                worker_ids.add(p.get("worker_id"))
            for b in it.get("worker_time_blocks", []) or []:
                worker_ids.add(b.get("worker_id"))
            assert wid in worker_ids, f"Reservation {it.get('id')} not linked to worker {wid}: {worker_ids}"

    def test_admin_reservations_full_access(self, admin_login):
        token = admin_login["access_token"]
        r = requests.get(f"{BASE_URL}/api/reservations", headers=_hdr(token))
        assert r.status_code == 200


# --- Worker cannot modify (RBAC) ---
class TestWorkerRBACDenies:
    def test_worker_cannot_create_reservation_via_admin_endpoint(self, worker_login):
        token = worker_login["access_token"]
        r = requests.post(f"{BASE_URL}/api/admin/reservations",
                          headers=_hdr(token),
                          json={"service_worker_pairs": [], "date": "2026-01-15",
                                "time": "10:00", "client_name": "X", "client_phone": "111"})
        assert r.status_code == 403

    def test_worker_cannot_update_settings(self, worker_login):
        token = worker_login["access_token"]
        r = requests.put(f"{BASE_URL}/api/settings", headers=_hdr(token),
                         json={"salon_name": "hack"})
        assert r.status_code == 403

    def test_worker_cannot_create_worker(self, worker_login):
        token = worker_login["access_token"]
        r = requests.post(f"{BASE_URL}/api/workers", headers=_hdr(token),
                         json={"name": "X", "services": [], "work_start": "09:00", "work_end": "17:00"})
        assert r.status_code == 403


# --- Worker account endpoints ---
class TestWorkerAccountEndpoints:
    def test_get_worker_account_exists_for_marija(self, admin_login, worker_login):
        token = admin_login["access_token"]
        wid = worker_login["worker_id"]
        r = requests.get(f"{BASE_URL}/api/workers/{wid}/account", headers=_hdr(token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("has_account") is True
        assert data.get("email") == WORKER_EMAIL

    def test_create_worker_account_duplicate_returns_409(self, admin_login, worker_login):
        token = admin_login["access_token"]
        wid = worker_login["worker_id"]
        r = requests.post(f"{BASE_URL}/api/workers/{wid}/create-account",
                          headers=_hdr(token),
                          json={"email": "someother_TEST@example.com", "language_preference": "sr"})
        # Worker already has account -> 409
        assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"

    def test_create_worker_account_duplicate_email_returns_409(self, admin_login):
        """Try to create an account for a different worker using an existing email."""
        token = admin_login["access_token"]
        # First get any worker
        wr = requests.get(f"{BASE_URL}/api/workers", headers=_hdr(token))
        assert wr.status_code == 200
        workers = wr.json()
        # Find worker without account or just use any
        target = None
        for w in workers:
            if w["name"] != "Marija":
                target = w
                break
        if not target:
            pytest.skip("No secondary worker to test duplicate email")
        r = requests.post(f"{BASE_URL}/api/workers/{target['id']}/create-account",
                          headers=_hdr(token),
                          json={"email": WORKER_EMAIL, "language_preference": "sr"})
        assert r.status_code == 409


# --- Change password ---
class TestChangePassword:
    def test_worker_change_password_then_restore(self, worker_login):
        token = worker_login["access_token"]
        new_pass = "TempPass_TEST_123!"
        r = requests.put(f"{BASE_URL}/api/auth/change-password",
                        headers=_hdr(token, tenant=False),
                        json={"new_password": new_pass})
        assert r.status_code == 200, r.text
        # Verify login with new password
        r2 = _login(WORKER_EMAIL, new_pass)
        assert r2.status_code == 200
        new_token = r2.json()["access_token"]
        # Restore original
        r3 = requests.put(f"{BASE_URL}/api/auth/change-password",
                         headers=_hdr(new_token, tenant=False),
                         json={"new_password": WORKER_PASS})
        assert r3.status_code == 200
        # Confirm restore worked
        r4 = _login(WORKER_EMAIL, WORKER_PASS)
        assert r4.status_code == 200
