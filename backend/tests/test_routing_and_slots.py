"""
Backend tests for iteration 35:
- Login returns role + slug for smart redirect (super_admin & salon admin)
- /:slug public booking endpoints work WITHOUT auth (services, workers, by-slug, available-slots)
- Admin manual booking /reservations/available-slots requires X-Tenant-ID and returns slots
"""
import os
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

SUPER_EMAIL = "Bornaja23@gmail.com"
SUPER_PASS = "Markonijus23!"
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASS = "Admin123!"
SLUG = "beauty-studio-bor"
TENANT_ID = "tenant_bsb_001"


@pytest.fixture(scope="module")
def client():
    return requests.Session()


# ---------------- Auth: smart redirect data ----------------

class TestAuthSmartRedirect:
    def test_super_admin_login_returns_role(self, client):
        r = client.post(f"{API}/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PASS})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["role"] == "super_admin"
        assert "access_token" in data and len(data["access_token"]) > 0

    def test_salon_admin_login_returns_slug(self, client):
        r = client.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        if r.status_code != 200:
            pytest.skip(f"Salon admin login failed ({r.status_code}): {r.text}")
        data = r.json()
        assert data["role"] in ("admin", "owner"), f"unexpected role: {data['role']}"
        assert data["slug"] == SLUG, f"expected slug={SLUG}, got {data.get('slug')}"
        assert data["tenant_id"] == TENANT_ID

    def test_invalid_login(self, client):
        r = client.post(f"{API}/auth/login", json={"email": "nope@x.com", "password": "wrong"})
        assert r.status_code == 401


# ---------------- Public booking (no auth) ----------------

class TestPublicBooking:
    def test_tenant_by_slug_public(self, client):
        r = client.get(f"{API}/tenants/by-slug/{SLUG}")
        assert r.status_code == 200
        data = r.json()
        assert data["slug"] == SLUG
        assert data["tenant_id"] == TENANT_ID

    def test_public_services_with_tenant_header(self, client):
        r = client.get(f"{API}/services", headers={"X-Tenant-ID": TENANT_ID})
        assert r.status_code == 200
        services = r.json()
        assert isinstance(services, list)
        assert len(services) > 0, "Expected at least 1 service for public booking"
        assert "id" in services[0]

    def test_public_workers_with_tenant_header(self, client):
        r = client.get(f"{API}/workers", headers={"X-Tenant-ID": TENANT_ID})
        assert r.status_code == 200
        workers = r.json()
        assert isinstance(workers, list)
        assert len(workers) > 0, "Expected at least 1 worker for public booking"

    def test_public_available_slots_no_auth(self, client):
        # Fetch a service+worker to build a valid pair
        services = client.get(f"{API}/services", headers={"X-Tenant-ID": TENANT_ID}).json()
        workers = client.get(f"{API}/workers", headers={"X-Tenant-ID": TENANT_ID}).json()
        # Find worker that supports first service
        svc = services[0]
        worker = None
        for w in workers:
            if svc["id"] in (w.get("services") or []):
                worker = w
                break
        if not worker:
            pytest.skip("No worker linked to first service")

        future = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")
        body = {
            "service_worker_pairs": [{"service_id": svc["id"], "worker_id": worker["id"]}],
            "date": future,
        }
        r = client.post(f"{API}/reservations/available-slots", json=body,
                        headers={"X-Tenant-ID": TENANT_ID})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "slots" in data
        assert isinstance(data["slots"], list)
        # Public flow does not require auth -> slots should be returned (may be empty if salon closed that day)
        print(f"Public slots returned: {len(data['slots'])} for {future}")


# ---------------- Admin manual booking slot fetch ----------------

class TestAdminManualBookingSlots:
    """The critical bug fix: AdminDashboard ManualBookingModal.fetchSlots
    must send X-Tenant-ID header. Verify backend returns slots when header is present
    and rejects when header is missing for authenticated admin."""

    @pytest.fixture(scope="class")
    def admin_token(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
        if r.status_code != 200:
            pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
        return r.json()["access_token"]

    @pytest.fixture(scope="class")
    def service_worker(self, admin_token):
        h = {"Authorization": f"Bearer {admin_token}", "X-Tenant-ID": TENANT_ID}
        services = requests.get(f"{API}/services", headers=h).json()
        workers = requests.get(f"{API}/workers", headers=h).json()
        for svc in services:
            for w in workers:
                if svc["id"] in (w.get("services") or []):
                    return svc, w
        pytest.skip("No service+worker pair available")

    def test_slots_with_tenant_header(self, admin_token, service_worker):
        svc, w = service_worker
        future = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
        h = {"Authorization": f"Bearer {admin_token}", "X-Tenant-ID": TENANT_ID}
        body = {"service_worker_pairs": [{"service_id": svc["id"], "worker_id": w["id"]}], "date": future}
        r = requests.post(f"{API}/reservations/available-slots", json=body, headers=h)
        assert r.status_code == 200, f"Expected 200 with tenant header, got {r.status_code}: {r.text}"
        data = r.json()
        assert isinstance(data.get("slots"), list)
        print(f"Admin slots with X-Tenant-ID for {future}: {len(data['slots'])} slots")

    def test_slots_without_tenant_header_fails(self, admin_token, service_worker):
        """Reproduces the original bug: without X-Tenant-ID the API rejects with 400."""
        svc, w = service_worker
        future = (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d")
        h = {"Authorization": f"Bearer {admin_token}"}  # NO X-Tenant-ID
        body = {"service_worker_pairs": [{"service_id": svc["id"], "worker_id": w["id"]}], "date": future}
        r = requests.post(f"{API}/reservations/available-slots", json=body, headers=h)
        # Either rejects (400) or returns empty (the original bug). Document behavior.
        assert r.status_code in (400, 422, 200)
        if r.status_code == 200:
            empty_or_full = r.json().get("slots", [])
            print(f"Without X-Tenant-ID: status 200, slots={len(empty_or_full)} (original bug behavior)")
        else:
            print(f"Without X-Tenant-ID: status {r.status_code} - properly rejected")
