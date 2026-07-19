"""
Tests for must_change_password flow:
- Login returns must_change_password field
- PUT /api/auth/change-password sets must_change_password to false and updates hash
- GET /api/auth/me returns must_change_password
"""
import os
import pytest
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://slot-reserve-23.preview.emergentagent.com').rstrip('/')
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

WORKER_EMAIL = "worker@salon.com"
ORIGINAL_PW = "Worker123!"
NEW_PW = "NewWorker456!"
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PW = "Admin123!"


@pytest.fixture(scope="module")
def mongo_db():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


@pytest.fixture
def set_worker_must_change(mongo_db):
    """Set must_change_password=True and reset hash on worker before test; restore after."""
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    orig_hash = pwd.hash(ORIGINAL_PW)
    mongo_db.users.update_one(
        {"email": WORKER_EMAIL},
        {"$set": {"must_change_password": True, "password_hash": orig_hash}}
    )
    yield
    # Restore
    mongo_db.users.update_one(
        {"email": WORKER_EMAIL},
        {"$set": {"must_change_password": False, "password_hash": orig_hash}}
    )


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    return r


class TestMustChangePasswordFlow:

    def test_admin_login_no_must_change(self):
        r = _login(ADMIN_EMAIL, ADMIN_PW)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("must_change_password") is False
        assert data.get("role") == "admin"
        assert "access_token" in data

    def test_worker_login_returns_must_change_true(self, set_worker_must_change):
        r = _login(WORKER_EMAIL, ORIGINAL_PW)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("must_change_password") is True
        assert data.get("role") == "worker"
        assert data.get("slug") == "beauty-studio-bor"

    def test_me_returns_must_change_password_field(self, set_worker_must_change):
        r = _login(WORKER_EMAIL, ORIGINAL_PW)
        token = r.json()["access_token"]
        me = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200, me.text
        assert me.json().get("must_change_password") is True

    def test_change_password_short_returns_400(self, set_worker_must_change):
        r = _login(WORKER_EMAIL, ORIGINAL_PW)
        token = r.json()["access_token"]
        resp = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": "abc"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_change_password_success_sets_flag_false_and_updates_hash(self, set_worker_must_change, mongo_db):
        r = _login(WORKER_EMAIL, ORIGINAL_PW)
        token = r.json()["access_token"]

        resp = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": NEW_PW},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text

        # Verify DB updated
        u = mongo_db.users.find_one({"email": WORKER_EMAIL})
        assert u["must_change_password"] is False

        # /me should now show false
        me = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json().get("must_change_password") is False

        # Old password no longer works
        r_old = _login(WORKER_EMAIL, ORIGINAL_PW)
        assert r_old.status_code == 401

        # New password works
        r_new = _login(WORKER_EMAIL, NEW_PW)
        assert r_new.status_code == 200
        assert r_new.json().get("must_change_password") is False

    def test_change_password_requires_auth(self):
        resp = requests.put(
            f"{BASE_URL}/api/auth/change-password",
            json={"new_password": "SomeNewPass123"},
        )
        assert resp.status_code in (401, 403)
