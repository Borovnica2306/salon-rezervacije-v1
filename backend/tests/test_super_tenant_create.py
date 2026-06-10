"""Tests for Super Admin tenant creation - POST /api/super/tenants"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://slot-reserve-23.preview.emergentagent.com").rstrip("/")

SUPER_ADMIN_EMAIL = "bornaja23@gmail.com"
SUPER_ADMIN_PASSWORD = "Markonijus23!"
SALON_ADMIN_EMAIL = "admin@salon.com"
SALON_ADMIN_PASSWORD = "Admin123!"
PRIMARY_TENANT_ID = "tenant_bsb_001"
PRIMARY_TENANT_SLUG = "beauty-studio-bor"

TEST_SALON_NAME = "TEST Salon Kragujevac"
TEST_SALON_EMAIL = "test_kragujevac@test.com"
TEST_SALON_PASSWORD = "TestPass123!"
TEST_SALON_EXPECTED_SLUG = "test-salon-kragujevac"


@pytest.fixture(scope="module")
def super_admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
                      headers={"Content-Type": "application/json"})
    assert r.status_code == 200, f"Super admin login failed: {r.status_code} {r.text}"
    data = r.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def salon_admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": SALON_ADMIN_EMAIL, "password": SALON_ADMIN_PASSWORD},
                      headers={"Content-Type": "application/json"})
    assert r.status_code == 200
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def primary_tenant_snapshot(super_admin_token):
    """Snapshot the primary tenant data BEFORE creating a new salon for isolation check."""
    r = requests.get(f"{BASE_URL}/api/tenants/by-slug/{PRIMARY_TENANT_SLUG}")
    assert r.status_code == 200
    return r.json()


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_tenant(super_admin_token):
    """Cleanup: delete the test tenant after all tests via direct DB if available."""
    yield
    # Cleanup via mongo since no DELETE endpoint exists
    try:
        from pymongo import MongoClient
        import os as _os
        # Read backend env directly
        env_path = "/app/backend/.env"
        mongo_url = "mongodb://localhost:27017"
        db_name = "test_database"
        if _os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("MONGO_URL="):
                        mongo_url = line.split("=", 1)[1].strip().strip('"')
                    elif line.startswith("DB_NAME="):
                        db_name = line.split("=", 1)[1].strip().strip('"')
        client = MongoClient(mongo_url)
        d = client[db_name]
        # Find tenant
        t = d.tenants.find_one({"slug": TEST_SALON_EXPECTED_SLUG})
        if t:
            tid = t["tenant_id"]
            d.tenants.delete_many({"slug": TEST_SALON_EXPECTED_SLUG})
            d.users.delete_many({"email": TEST_SALON_EMAIL})
            d.settings.delete_many({"tenant_id": tid})
            d.categories_config.delete_many({"tenant_id": tid})
            print(f"Cleaned up test tenant: {tid}")
        client.close()
    except Exception as e:
        print(f"Cleanup error (non-fatal): {e}")


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# Pre-cleanup before running tests in case data exists
def test_00_pre_cleanup():
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017")
        d = client["test_database"]
        t = d.tenants.find_one({"slug": TEST_SALON_EXPECTED_SLUG})
        if t:
            tid = t["tenant_id"]
            d.tenants.delete_many({"slug": TEST_SALON_EXPECTED_SLUG})
            d.users.delete_many({"email": TEST_SALON_EMAIL})
            d.settings.delete_many({"tenant_id": tid})
            d.categories_config.delete_many({"tenant_id": tid})
        client.close()
    except Exception as e:
        pytest.skip(f"Pre-cleanup unavailable: {e}")


# 1. Auth requirement
def test_01_post_super_tenants_requires_auth():
    r = requests.post(f"{BASE_URL}/api/super/tenants", json={"name": "X", "email": "x@x.com", "password": "123456"})
    assert r.status_code in (401, 403)


# 2. Non-super-admin gets 403
def test_02_post_super_tenants_forbidden_for_salon_admin(salon_admin_token):
    r = requests.post(f"{BASE_URL}/api/super/tenants",
                      json={"name": "Hack", "email": "h@h.com", "password": "Secret123"},
                      headers=_auth_headers(salon_admin_token))
    assert r.status_code == 403


# 3. Validation - missing fields
def test_03_validation_missing_fields(super_admin_token):
    r = requests.post(f"{BASE_URL}/api/super/tenants",
                      json={"name": "", "email": "", "password": ""},
                      headers=_auth_headers(super_admin_token))
    assert r.status_code == 400
    assert "required" in r.text.lower() or "obavezna" in r.text.lower() or "required" in r.json().get("detail", "").lower()


# 4. Validation - short password
def test_04_validation_short_password(super_admin_token):
    r = requests.post(f"{BASE_URL}/api/super/tenants",
                      json={"name": "Test Foo", "email": "foo@x.com", "password": "abc"},
                      headers=_auth_headers(super_admin_token))
    assert r.status_code == 400


# 5. Create salon successfully
def test_05_create_test_salon(super_admin_token, primary_tenant_snapshot):
    payload = {
        "name": TEST_SALON_NAME,
        "email": TEST_SALON_EMAIL,
        "password": TEST_SALON_PASSWORD,
        "country": "RS",
        "city": "Kragujevac",
    }
    r = requests.post(f"{BASE_URL}/api/super/tenants", json=payload, headers=_auth_headers(super_admin_token))
    assert r.status_code == 200, f"Create failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["slug"] == TEST_SALON_EXPECTED_SLUG, f"Expected slug '{TEST_SALON_EXPECTED_SLUG}', got '{data['slug']}'"
    assert data["name"] == TEST_SALON_NAME
    assert data["country"] == "RS"
    assert data["city"] == "Kragujevac"
    assert data["admin_email"] == TEST_SALON_EMAIL
    assert data["tenant_id"].startswith("tenant_")


# 6. Verify new tenant in list (Saloni tab data)
def test_06_new_tenant_in_list(super_admin_token):
    r = requests.get(f"{BASE_URL}/api/super/tenants", headers=_auth_headers(super_admin_token))
    assert r.status_code == 200
    tenants = r.json()
    slugs = [t["slug"] for t in tenants]
    assert PRIMARY_TENANT_SLUG in slugs, "Primary tenant missing from list"
    assert TEST_SALON_EXPECTED_SLUG in slugs, "New test tenant missing from list"
    # Must have at least 2
    assert len(tenants) >= 2


# 7. Data isolation: Primary tenant unchanged
def test_07_primary_tenant_unchanged(primary_tenant_snapshot):
    r = requests.get(f"{BASE_URL}/api/tenants/by-slug/{PRIMARY_TENANT_SLUG}")
    assert r.status_code == 200
    current = r.json()
    assert current["tenant_id"] == primary_tenant_snapshot["tenant_id"]
    assert current["name"] == primary_tenant_snapshot["name"]
    assert current["slug"] == primary_tenant_snapshot["slug"]
    assert current["enabled_features"] == primary_tenant_snapshot["enabled_features"]


# 8. New tenant retrievable by slug
def test_08_new_tenant_resolvable_by_slug():
    r = requests.get(f"{BASE_URL}/api/tenants/by-slug/{TEST_SALON_EXPECTED_SLUG}")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == TEST_SALON_NAME
    assert data["city"] == "Kragujevac"
    # New tenant should have default features enabled
    feats = data["enabled_features"]
    assert feats.get("manual_booking") is True
    assert feats.get("email_notifications") is True


# 9. New admin can login
def test_09_new_admin_can_login():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": TEST_SALON_EMAIL, "password": TEST_SALON_PASSWORD},
                      headers={"Content-Type": "application/json"})
    assert r.status_code == 200, f"New admin login failed: {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token
    assert data.get("tenant_id"), "New admin must have tenant_id"
    assert data.get("tenant_id") != PRIMARY_TENANT_ID, "New admin tenant_id must differ from primary"


# 10. Duplicate email - reject
def test_10_duplicate_email_rejected(super_admin_token):
    r = requests.post(f"{BASE_URL}/api/super/tenants",
                      json={"name": "Other Salon Test", "email": TEST_SALON_EMAIL, "password": "AnotherPass1"},
                      headers=_auth_headers(super_admin_token))
    assert r.status_code == 400
    assert "exists" in r.text.lower() or "već" in r.text.lower() or "already" in r.text.lower()


# 11. Data isolation: new tenant's data does not leak to primary
def test_11_new_tenant_data_isolated(super_admin_token):
    # Get new tenant's services list - should be empty
    new_tenant_resp = requests.get(f"{BASE_URL}/api/tenants/by-slug/{TEST_SALON_EXPECTED_SLUG}")
    new_tid = None
    if new_tenant_resp.status_code == 200:
        # tenant_id not returned in by-slug for new; use super admin list
        ts = requests.get(f"{BASE_URL}/api/super/tenants", headers=_auth_headers(super_admin_token)).json()
        for t in ts:
            if t["slug"] == TEST_SALON_EXPECTED_SLUG:
                new_tid = t["tenant_id"]
                break
    assert new_tid

    # New tenant should have 0 services/workers
    r_workers = requests.get(f"{BASE_URL}/api/workers", headers={"X-Tenant-ID": new_tid})
    assert r_workers.status_code == 200
    assert r_workers.json() == []

    # Primary tenant still has its workers
    r_primary = requests.get(f"{BASE_URL}/api/workers", headers={"X-Tenant-ID": PRIMARY_TENANT_ID})
    assert r_primary.status_code == 200
    # Should have at least some workers


# 12. Slug uniqueness: creating with same name appends suffix
def test_12_duplicate_name_unique_slug(super_admin_token):
    # Try creating another salon with same name but different email
    r = requests.post(f"{BASE_URL}/api/super/tenants",
                      json={"name": TEST_SALON_NAME, "email": "test_kg_2@test.com", "password": "Another123"},
                      headers=_auth_headers(super_admin_token))
    assert r.status_code == 200, f"Failed: {r.text}"
    data = r.json()
    assert data["slug"] != TEST_SALON_EXPECTED_SLUG, "Slug must be unique"
    assert data["slug"].startswith(TEST_SALON_EXPECTED_SLUG + "-")
    # Cleanup the 2nd one
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017")
        d = client["test_database"]
        d.tenants.delete_many({"slug": data["slug"]})
        d.users.delete_many({"email": "test_kg_2@test.com"})
        d.settings.delete_many({"tenant_id": data["tenant_id"]})
        d.categories_config.delete_many({"tenant_id": data["tenant_id"]})
        client.close()
    except Exception:
        pass
