"""Tests for Super Admin God Mode endpoints: status, owner-password, feature isolation."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://slot-reserve-23.preview.emergentagent.com").rstrip("/")
SUPER_EMAIL = "Bornaja23@gmail.com"
SUPER_PASS = "Markonijus23!"
SALON_OWNER_EMAIL = "admin@salon.com"
SALON_OWNER_PASS = "Admin123!"
PRIMARY_TENANT_ID = "tenant_bsb_001"


@pytest.fixture(scope="module")
def super_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PASS})
    assert r.status_code == 200, f"Super admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def super_headers(super_token):
    return {"Authorization": f"Bearer {super_token}"}


@pytest.fixture(scope="module")
def tenants(super_headers):
    r = requests.get(f"{BASE_URL}/api/super/tenants", headers=super_headers)
    assert r.status_code == 200
    return r.json()


def _find_tenant(tenants, tid):
    for t in tenants:
        if t["tenant_id"] == tid:
            return t
    return None


def test_super_login_and_list(super_headers, tenants):
    assert len(tenants) >= 1
    primary = _find_tenant(tenants, PRIMARY_TENANT_ID)
    assert primary is not None, f"Primary tenant {PRIMARY_TENANT_ID} not present"
    assert primary["slug"] == "beauty-studio-bor"


def test_status_toggle_suspend_then_active(super_headers):
    # Suspend
    r = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/status",
                     json={"status": "suspended"}, headers=super_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "suspended"

    # Verify via list
    listing = requests.get(f"{BASE_URL}/api/super/tenants", headers=super_headers).json()
    assert _find_tenant(listing, PRIMARY_TENANT_ID).get("status") == "suspended"

    # Re-activate
    r2 = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/status",
                      json={"status": "active"}, headers=super_headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "active"


def test_status_invalid_value(super_headers):
    r = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/status",
                     json={"status": "garbage"}, headers=super_headers)
    assert r.status_code == 400


def test_status_unknown_tenant(super_headers):
    r = requests.put(f"{BASE_URL}/api/super/tenants/does_not_exist/status",
                     json={"status": "active"}, headers=super_headers)
    assert r.status_code == 404


def test_status_requires_super_admin():
    # Login as salon admin if available
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": SALON_OWNER_EMAIL, "password": SALON_OWNER_PASS})
    if r.status_code != 200:
        pytest.skip(f"Salon admin login unavailable: {r.status_code}")
    token = r.json()["access_token"]
    r2 = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/status",
                      json={"status": "active"},
                      headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 403


def test_owner_password_change_and_login(super_headers):
    """The endpoint updates user matching tenant.owner_email. For tenant_bsb_001
    owner_email is the super-admin's own email (Bornaja23@gmail.com), so we
    test on that account. NOTE: this is a security concern - changing the
    'owner password' from the Beauty Studio Bor God Mode page actually
    changes the super admin's own login password."""
    # Read actual owner_email from tenant
    listing = requests.get(f"{BASE_URL}/api/super/tenants", headers=super_headers).json()
    primary = _find_tenant(listing, PRIMARY_TENANT_ID)
    owner_email = primary["owner_email"]

    original_pw = SUPER_PASS if owner_email.lower() == SUPER_EMAIL.lower() else SALON_OWNER_PASS
    new_pw = "Tmp123!Pw"

    r = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/owner-password",
                     json={"password": new_pw}, headers=super_headers)
    assert r.status_code == 200, r.text
    assert r.json()["email"].lower() == owner_email.lower()

    # New password works
    login_new = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": owner_email, "password": new_pw})
    assert login_new.status_code == 200, f"Login with new pw failed: {login_new.text}"

    # Restore original password (re-login as super may be needed if we changed super's pw)
    if owner_email.lower() == SUPER_EMAIL.lower():
        new_token = login_new.json()["access_token"]
        restore_headers = {"Authorization": f"Bearer {new_token}"}
    else:
        restore_headers = super_headers

    restore = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/owner-password",
                           json={"password": original_pw}, headers=restore_headers)
    assert restore.status_code == 200
    confirm = requests.post(f"{BASE_URL}/api/auth/login",
                            json={"email": owner_email, "password": original_pw})
    assert confirm.status_code == 200, "Password restore did not succeed"


def test_owner_password_too_short(super_headers):
    r = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/owner-password",
                     json={"password": "abc"}, headers=super_headers)
    assert r.status_code == 400


def test_feature_flag_isolation(super_headers, tenants):
    """Toggle a feature on primary tenant, ensure other tenants are NOT modified."""
    if len(tenants) < 2:
        pytest.skip("Need at least 2 tenants for isolation test")

    other = next((t for t in tenants if t["tenant_id"] != PRIMARY_TENANT_ID), None)
    assert other is not None

    # Capture baseline
    primary = _find_tenant(tenants, PRIMARY_TENANT_ID)
    primary_features = dict(primary.get("enabled_features", {}))
    other_features_before = dict(other.get("enabled_features", {}))

    # Flip ips_qr_payment on primary
    key = "ips_qr_payment"
    new_val = not primary_features.get(key, True)
    new_features = {**primary_features, key: new_val}
    r = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/features",
                     json=new_features, headers=super_headers)
    assert r.status_code == 200, r.text

    # Re-fetch
    listing = requests.get(f"{BASE_URL}/api/super/tenants", headers=super_headers).json()
    primary_after = _find_tenant(listing, PRIMARY_TENANT_ID)
    other_after = _find_tenant(listing, other["tenant_id"])
    assert primary_after["enabled_features"].get(key) == new_val
    assert other_after["enabled_features"] == other_features_before, "Isolation breach: other tenant features changed"

    # Restore
    requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/features",
                 json=primary_features, headers=super_headers)


def test_category_toggle_isolation(super_headers, tenants):
    """Toggle a category on primary tenant via X-Tenant-ID, ensure another tenant unaffected."""
    if len(tenants) < 2:
        pytest.skip("Need 2 tenants")
    other = next((t for t in tenants if t["tenant_id"] != PRIMARY_TENANT_ID), None)

    def get_cats(tid):
        r = requests.get(f"{BASE_URL}/api/categories/config",
                         headers={**super_headers, "X-Tenant-ID": tid})
        assert r.status_code == 200, r.text
        return r.json()

    primary_cats = get_cats(PRIMARY_TENANT_ID)
    other_cats_before = get_cats(other["tenant_id"])

    assert len(primary_cats) > 0
    target = primary_cats[0]
    new_state = not target["enabled"]

    # Toggle
    r = requests.put(f"{BASE_URL}/api/categories/config",
                     json={"category": target["key"], "enabled": new_state},
                     headers={**super_headers, "X-Tenant-ID": PRIMARY_TENANT_ID})
    assert r.status_code == 200, r.text

    primary_after = get_cats(PRIMARY_TENANT_ID)
    other_after = get_cats(other["tenant_id"])

    target_after = next(c for c in primary_after if c["key"] == target["key"])
    assert target_after["enabled"] == new_state

    # Other tenant unchanged
    def _norm(cs): return {c["key"]: c["enabled"] for c in cs}
    assert _norm(other_after) == _norm(other_cats_before), "Category isolation breach"

    # Restore
    requests.put(f"{BASE_URL}/api/categories/config",
                 json={"category": target["key"], "enabled": target["enabled"]},
                 headers={**super_headers, "X-Tenant-ID": PRIMARY_TENANT_ID})


def test_unauthenticated_blocked():
    r = requests.put(f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/status",
                     json={"status": "active"})
    assert r.status_code in (401, 403)
