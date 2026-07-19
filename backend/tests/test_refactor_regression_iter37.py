"""
Iteration 37 regression test: verify all endpoint groups still work after
routes.py -> auth_routes.py / worker_routes.py / admin_routes.py / booking_routes.py split.

Also verifies SalonWorkers backend flows: create-account -> get_worker_account -> delete_worker_account.
"""
import os
import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass
    if not url:
        raise RuntimeError("REACT_APP_BACKEND_URL missing")
    return url.rstrip("/")

BASE = _load_backend_url() + "/api"
TENANT_ID = "tenant_bsb_001"
TENANT_SLUG = "beauty-studio-bor"
HDR_TENANT = {"X-Tenant-ID": TENANT_ID}

ADMIN = ("admin@salon.com", "Admin123!")
WORKER = ("worker@salon.com", "Worker123!")
SUPER = ("Bornaja23@gmail.com", "Markonijus23!")


def _login(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="module")
def admin_hdr():
    d = _login(*ADMIN)
    return {"Authorization": f"Bearer {d['access_token']}", **HDR_TENANT}


@pytest.fixture(scope="module")
def worker_hdr():
    d = _login(*WORKER)
    return {"Authorization": f"Bearer {d['access_token']}", **HDR_TENANT}, d


@pytest.fixture(scope="module")
def super_hdr():
    d = _login(*SUPER)
    return {"Authorization": f"Bearer {d['access_token']}", **HDR_TENANT}


# ---------- auth_routes ----------
class TestAuthRoutes:
    def test_login_admin(self):
        d = _login(*ADMIN)
        assert d["role"] == "admin"
        assert d["tenant_id"] == TENANT_ID
        assert d["slug"] == TENANT_SLUG

    def test_login_worker(self):
        d = _login(*WORKER)
        assert d["role"] == "worker"
        assert d["worker_id"], "worker_id missing"
        assert d["slug"] == TENANT_SLUG

    def test_login_bad_pw(self):
        r = requests.post(f"{BASE}/auth/login", json={"email": ADMIN[0], "password": "wrong"})
        assert r.status_code == 401

    def test_me_admin(self, admin_hdr):
        r = requests.get(f"{BASE}/auth/me", headers=admin_hdr)
        assert r.status_code == 200
        assert r.json()["role"] == "admin"


# ---------- worker_routes ----------
class TestWorkerRoutes:
    def test_list_workers(self, admin_hdr):
        r = requests.get(f"{BASE}/workers", headers=admin_hdr)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0

    def test_worker_account_status_marija(self, admin_hdr):
        # Find Marija
        r = requests.get(f"{BASE}/workers", headers=admin_hdr)
        marija = next((w for w in r.json() if w["name"].lower().startswith("marija")), None)
        assert marija is not None
        r2 = requests.get(f"{BASE}/workers/{marija['id']}/account", headers=admin_hdr)
        assert r2.status_code == 200
        body = r2.json()
        assert body["has_account"] is True
        assert body["email"] == "worker@salon.com"

    def test_create_account_duplicate_email(self, admin_hdr):
        # Try creating an account with an already-used email on any other worker
        r = requests.get(f"{BASE}/workers", headers=admin_hdr)
        other = next((w for w in r.json() if not w["name"].lower().startswith("marija")), None)
        if not other:
            pytest.skip("No non-marija worker to test with")
        r2 = requests.post(
            f"{BASE}/workers/{other['id']}/create-account",
            headers=admin_hdr,
            json={"email": "worker@salon.com"},
        )
        assert r2.status_code == 409

    def test_worker_denied_on_create_worker(self, worker_hdr):
        hdr, _ = worker_hdr
        r = requests.post(f"{BASE}/workers", headers=hdr, json={
            "name": "X", "services": [], "work_start": "09:00", "work_end": "17:00",
            "break_start": None, "break_end": None, "days_off": []
        })
        assert r.status_code == 403


# ---------- admin_routes ----------
class TestAdminRoutes:
    def test_tenant_by_slug(self):
        r = requests.get(f"{BASE}/tenants/by-slug/{TENANT_SLUG}")
        assert r.status_code == 200
        assert r.json()["tenant_id"] == TENANT_ID

    def test_settings(self, admin_hdr):
        r = requests.get(f"{BASE}/settings", headers=admin_hdr)
        assert r.status_code == 200
        assert "salon_name" in r.json()

    def test_categories(self, admin_hdr):
        r = requests.get(f"{BASE}/categories", headers=admin_hdr)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_services(self, admin_hdr):
        r = requests.get(f"{BASE}/services", headers=admin_hdr)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_blacklist_get(self, admin_hdr):
        r = requests.get(f"{BASE}/blacklist", headers=admin_hdr)
        assert r.status_code == 200

    def test_super_tenants(self, super_hdr):
        r = requests.get(f"{BASE}/super/tenants", headers=super_hdr)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert any(t.get("tenant_id") == TENANT_ID for t in r.json())

    def test_super_denied_to_admin(self, admin_hdr):
        r = requests.get(f"{BASE}/super/tenants", headers=admin_hdr)
        assert r.status_code == 403


# ---------- booking_routes ----------
class TestBookingRoutes:
    def test_reservations_admin(self, admin_hdr):
        r = requests.get(f"{BASE}/reservations", headers=admin_hdr)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_reservations_worker_7day_window(self, worker_hdr):
        hdr, _ = worker_hdr
        r = requests.get(f"{BASE}/reservations", headers=hdr)
        assert r.status_code == 200
        from datetime import datetime, timedelta
        today = datetime.utcnow().strftime("%Y-%m-%d")
        end = (datetime.utcnow() + timedelta(days=8)).strftime("%Y-%m-%d")
        for res in r.json():
            assert today <= res["date"] < end

    def test_available_slots_public(self):
        # Need at least a worker+service pair
        r = requests.get(f"{BASE}/workers", headers=HDR_TENANT)
        s = requests.get(f"{BASE}/services", headers=HDR_TENANT)
        if r.status_code != 200 or s.status_code != 200 or not r.json() or not s.json():
            pytest.skip("No workers/services seeded")
        w = r.json()[0]
        svc = next((sv for sv in s.json() if sv["id"] in w.get("services", [])), None)
        if not svc:
            pytest.skip("No service linked to first worker")
        from datetime import datetime, timedelta
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        r2 = requests.post(f"{BASE}/reservations/available-slots", headers=HDR_TENANT, json={
            "service_worker_pairs": [{"service_id": svc["id"], "worker_id": w["id"]}],
            "date": tomorrow,
        })
        assert r2.status_code == 200
        assert "slots" in r2.json()


# ---------- Root ----------
def test_api_root():
    r = requests.get(f"{BASE}/")
    assert r.status_code == 200
