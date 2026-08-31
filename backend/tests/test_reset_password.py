"""
Tests for PUT /api/workers/{worker_id}/reset-password endpoint (iteration 39).
Restores worker@salon.com to Worker123!/must_change_password=false after tests.
"""
import os
import pytest
import requests
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv

# Ensure MONGO_URL/DB_NAME are available when this module runs standalone
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://slot-reserve-23.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
TENANT_ID = "tenant_bsb_001"
TENANT_SLUG = "beauty-studio-bor"

ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASS = "Admin123!"
WORKER_EMAIL = "worker@salon.com"
WORKER_PASS = "Worker123!"

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password},
                      headers={"X-Tenant-Id": TENANT_ID})
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN_EMAIL, ADMIN_PASS)


@pytest.fixture(scope="module")
def worker_token():
    return _login(WORKER_EMAIL, WORKER_PASS)


@pytest.fixture(scope="module")
def marija_worker_id(admin_token):
    r = requests.get(f"{API}/workers?active_only=false",
                     headers={"Authorization": f"Bearer {admin_token}", "X-Tenant-Id": TENANT_ID})
    assert r.status_code == 200
    workers = r.json()
    m = next((w for w in workers if w["name"].lower().startswith("marija")), None)
    assert m, f"Marija not found. Workers: {[w['name'] for w in workers]}"
    return m["id"]


@pytest.fixture(scope="module", autouse=True)
def restore_worker_after():
    yield
    # Restore worker@salon.com to Worker123! and must_change_password=false
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    async def restore():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        await db.users.update_one(
            {"email": WORKER_EMAIL},
            {"$set": {
                "password_hash": pwd_ctx.hash(WORKER_PASS),
                "must_change_password": False,
            }}
        )
        client.close()

    asyncio.run(restore())


def test_reset_password_admin_success(admin_token, marija_worker_id):
    r = requests.put(
        f"{API}/workers/{marija_worker_id}/reset-password",
        headers={"Authorization": f"Bearer {admin_token}", "X-Tenant-Id": TENANT_ID},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "temp_password" in data
    assert isinstance(data["temp_password"], str)
    assert len(data["temp_password"]) >= 6
    assert data["email"] == WORKER_EMAIL

    # Verify DB flag
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    async def check():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        u = await db.users.find_one({"email": WORKER_EMAIL})
        client.close()
        return u

    u = asyncio.run(check())
    assert u["must_change_password"] is True

    # Verify new password works
    r2 = requests.post(f"{API}/auth/login",
                       json={"email": WORKER_EMAIL, "password": data["temp_password"]},
                       headers={"X-Tenant-Id": TENANT_ID})
    assert r2.status_code == 200


def test_reset_password_nonexistent_worker(admin_token):
    # Valid ObjectId format but non-existent
    fake_id = "507f1f77bcf86cd799439011"
    r = requests.put(
        f"{API}/workers/{fake_id}/reset-password",
        headers={"Authorization": f"Bearer {admin_token}", "X-Tenant-Id": TENANT_ID},
    )
    assert r.status_code == 404


def test_reset_password_worker_forbidden(marija_worker_id):
    # Re-login worker after previous reset changed password
    # Get fresh worker token via restore-and-login pattern: first restore then login
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")

    async def restore_now():
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        await db.users.update_one(
            {"email": WORKER_EMAIL},
            {"$set": {"password_hash": pwd_ctx.hash(WORKER_PASS), "must_change_password": False}}
        )
        client.close()

    asyncio.run(restore_now())
    wt = _login(WORKER_EMAIL, WORKER_PASS)

    r = requests.put(
        f"{API}/workers/{marija_worker_id}/reset-password",
        headers={"Authorization": f"Bearer {wt}", "X-Tenant-Id": TENANT_ID},
    )
    assert r.status_code == 403
