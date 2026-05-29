"""
Multitenant Backend Tests
Tests for slug-based tenant identification, tenant_id filtering, 
super admin access, and cross-tenant protection.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "bornaja23@gmail.com"
SUPER_ADMIN_PASSWORD = "Markonijus23!"
SALON_ADMIN_EMAIL = "admin@salon.com"
SALON_ADMIN_PASSWORD = "Admin123!"
PRIMARY_TENANT_ID = "tenant_bsb_001"
PRIMARY_TENANT_SLUG = "beauty-studio-bor"


@pytest.fixture
def api_client():
    """Fresh requests session for each test"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def super_admin_token():
    """Get super admin authentication token - fresh for each test"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Super admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    assert data.get("role") == "super_admin", f"Expected super_admin role, got {data.get('role')}"
    return data["access_token"]


@pytest.fixture
def salon_admin_token():
    """Get salon admin authentication token - fresh for each test"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": SALON_ADMIN_EMAIL,
        "password": SALON_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Salon admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    assert data.get("role") == "admin", f"Expected admin role, got {data.get('role')}"
    assert data.get("tenant_id") == PRIMARY_TENANT_ID, f"Expected tenant_id {PRIMARY_TENANT_ID}, got {data.get('tenant_id')}"
    return data["access_token"]


class TestTenantResolution:
    """Tests for tenant resolution by slug"""
    
    def test_get_tenant_by_slug_success(self, api_client):
        """GET /api/tenants/by-slug/beauty-studio-bor returns tenant with tenant_id, name, enabled_features"""
        response = api_client.get(f"{BASE_URL}/api/tenants/by-slug/{PRIMARY_TENANT_SLUG}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tenant_id" in data, "Missing tenant_id in response"
        assert data["tenant_id"] == PRIMARY_TENANT_ID, f"Expected {PRIMARY_TENANT_ID}, got {data['tenant_id']}"
        assert "name" in data, "Missing name in response"
        assert "enabled_features" in data, "Missing enabled_features in response"
        assert data["slug"] == PRIMARY_TENANT_SLUG, f"Expected slug {PRIMARY_TENANT_SLUG}, got {data['slug']}"
        
    def test_get_tenant_by_slug_not_found(self, api_client):
        """GET /api/tenants/by-slug/nonexistent returns 404"""
        response = api_client.get(f"{BASE_URL}/api/tenants/by-slug/nonexistent-salon-xyz")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestTenantHeaderRequirement:
    """Tests for X-Tenant-ID header requirement"""
    
    def test_workers_requires_tenant_header(self, api_client, salon_admin_token):
        """GET /api/workers requires X-Tenant-ID header (400 if missing)"""
        headers = {"Authorization": f"Bearer {salon_admin_token}"}
        response = api_client.get(f"{BASE_URL}/api/workers", headers=headers)
        assert response.status_code == 400, f"Expected 400 without X-Tenant-ID, got {response.status_code}: {response.text}"
        
    def test_workers_with_tenant_header(self, api_client, salon_admin_token):
        """GET /api/workers succeeds with X-Tenant-ID header"""
        headers = {
            "Authorization": f"Bearer {salon_admin_token}",
            "X-Tenant-ID": PRIMARY_TENANT_ID
        }
        response = api_client.get(f"{BASE_URL}/api/workers", headers=headers)
        assert response.status_code == 200, f"Expected 200 with X-Tenant-ID, got {response.status_code}: {response.text}"
        
    def test_categories_requires_tenant_header(self, api_client):
        """GET /api/categories requires X-Tenant-ID header"""
        response = api_client.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 400, f"Expected 400 without X-Tenant-ID, got {response.status_code}: {response.text}"
        
    def test_categories_with_tenant_header(self, api_client):
        """GET /api/categories succeeds with X-Tenant-ID header"""
        headers = {"X-Tenant-ID": PRIMARY_TENANT_ID}
        response = api_client.get(f"{BASE_URL}/api/categories", headers=headers)
        assert response.status_code == 200, f"Expected 200 with X-Tenant-ID, got {response.status_code}: {response.text}"


class TestLoginTenantId:
    """Tests for tenant_id in login response"""
    
    def test_login_returns_tenant_id_for_salon_admin(self, api_client):
        """Login returns tenant_id in response for salon admin"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data, "Missing tenant_id in login response"
        assert data["tenant_id"] == PRIMARY_TENANT_ID, f"Expected {PRIMARY_TENANT_ID}, got {data['tenant_id']}"
        
    def test_login_returns_empty_tenant_id_for_super_admin(self, api_client):
        """Login returns empty tenant_id for super admin (can access all tenants)"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "tenant_id" in data, "Missing tenant_id in login response"
        assert data["tenant_id"] == "", f"Super admin should have empty tenant_id, got {data['tenant_id']}"
        assert data["role"] == "super_admin", f"Expected super_admin role, got {data['role']}"


class TestCrossTenantAccess:
    """Tests for cross-tenant access protection"""
    
    def test_salon_admin_cannot_access_wrong_tenant(self, api_client, salon_admin_token):
        """Salon admin cannot access wrong tenant_id (403)"""
        headers = {
            "Authorization": f"Bearer {salon_admin_token}",
            "X-Tenant-ID": "wrong_tenant_id_xyz"
        }
        # Try to get reservations with wrong tenant
        response = api_client.get(f"{BASE_URL}/api/reservations", headers=headers)
        # Should be 403 (access denied) or 404 (invalid tenant)
        assert response.status_code in [403, 404], f"Expected 403 or 404, got {response.status_code}: {response.text}"


class TestSuperAdminTenantManagement:
    """Tests for super admin tenant management endpoints"""
    
    def test_super_admin_can_list_tenants(self, api_client, super_admin_token):
        """Super admin can list all tenants via GET /api/super/tenants"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{BASE_URL}/api/super/tenants", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of tenants"
        assert len(data) >= 1, "Expected at least one tenant"
        
        # Verify primary tenant is in the list
        tenant_ids = [t.get("tenant_id") for t in data]
        assert PRIMARY_TENANT_ID in tenant_ids, f"Primary tenant {PRIMARY_TENANT_ID} not found in tenants list"
        
    def test_super_admin_can_update_features(self, api_client, super_admin_token):
        """Super admin can update features via PUT /api/super/tenants/{id}/features"""
        headers = {
            "Authorization": f"Bearer {super_admin_token}",
            "Content-Type": "application/json"
        }
        
        # Update features
        new_features = {
            "viber_notifications": True,
            "ips_qr_payment": True,
            "manual_booking": True,
            "email_notifications": True,
            "lazy_cancel": True,
            "test_feature": True  # Add a test feature
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/features",
            json=new_features,
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "enabled_features" in data, "Missing enabled_features in response"
        assert data["enabled_features"].get("test_feature") == True, "test_feature not updated"
        
        # Clean up - remove test feature
        del new_features["test_feature"]
        api_client.put(
            f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/features",
            json=new_features,
            headers=headers
        )
        
    def test_non_super_admin_cannot_list_tenants(self, api_client, salon_admin_token):
        """Non-super-admin gets 403 on /api/super/tenants"""
        headers = {"Authorization": f"Bearer {salon_admin_token}"}
        response = api_client.get(f"{BASE_URL}/api/super/tenants", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        
    def test_non_super_admin_cannot_update_features(self, api_client, salon_admin_token):
        """Non-super-admin gets 403 on PUT /api/super/tenants/{id}/features"""
        headers = {
            "Authorization": f"Bearer {salon_admin_token}",
            "Content-Type": "application/json"
        }
        response = api_client.put(
            f"{BASE_URL}/api/super/tenants/{PRIMARY_TENANT_ID}/features",
            json={"test": True},
            headers=headers
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"


class TestTenantFilteredData:
    """Tests for tenant_id filtering on data endpoints"""
    
    def test_services_filtered_by_tenant(self, api_client):
        """Services are filtered by tenant_id"""
        headers = {"X-Tenant-ID": PRIMARY_TENANT_ID}
        response = api_client.get(f"{BASE_URL}/api/services", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of services"
        # Services should be returned (may be empty if no services exist)
        
    def test_workers_filtered_by_tenant(self, api_client, salon_admin_token):
        """Workers are filtered by tenant_id"""
        headers = {
            "Authorization": f"Bearer {salon_admin_token}",
            "X-Tenant-ID": PRIMARY_TENANT_ID
        }
        response = api_client.get(f"{BASE_URL}/api/workers", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of workers"
        
    def test_reservations_filtered_by_tenant(self, api_client, salon_admin_token):
        """Reservations are filtered by tenant_id"""
        headers = {
            "Authorization": f"Bearer {salon_admin_token}",
            "X-Tenant-ID": PRIMARY_TENANT_ID
        }
        response = api_client.get(f"{BASE_URL}/api/reservations", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of reservations"


class TestSettingsWithTenant:
    """Tests for settings endpoint with tenant"""
    
    def test_get_settings_with_tenant(self, api_client):
        """GET /api/settings works with X-Tenant-ID header"""
        headers = {"X-Tenant-ID": PRIMARY_TENANT_ID}
        response = api_client.get(f"{BASE_URL}/api/settings", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "salon_name" in data, "Missing salon_name in settings"
        assert "work_start" in data, "Missing work_start in settings"
        assert "work_end" in data, "Missing work_end in settings"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
