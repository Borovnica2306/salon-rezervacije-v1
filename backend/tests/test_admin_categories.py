"""
Test Multi-Level Admin System and Master Category Switch
Tests for:
- Super-Admin login and role verification
- Salon-Admin login and role verification
- Categories endpoints (public and config)
- Category toggle functionality
- Service filtering by enabled categories
- Access control for super_admin vs admin roles
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
SUPER_ADMIN_EMAIL = "bornaja23@gmail.com"
SUPER_ADMIN_PASSWORD = "Markonijus23!"
SALON_ADMIN_EMAIL = "admin@salon.com"
SALON_ADMIN_PASSWORD = "Admin123!"


class TestAuthRoles:
    """Test authentication and role verification for both admin types"""
    
    def test_super_admin_login_success(self):
        """Super-Admin login works with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super-Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["email"].lower() == SUPER_ADMIN_EMAIL.lower()
        print(f"✓ Super-Admin login successful: {data['email']}")
    
    def test_super_admin_role_is_super_admin(self):
        """Super-Admin role is 'super_admin' in /auth/me response"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Check /auth/me
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data["role"] == "super_admin", f"Expected role 'super_admin', got '{data.get('role')}'"
        print(f"✓ Super-Admin role verified: {data['role']}")
    
    def test_salon_admin_login_success(self):
        """Salon-Admin login works with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Salon-Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["email"].lower() == SALON_ADMIN_EMAIL.lower()
        print(f"✓ Salon-Admin login successful: {data['email']}")
    
    def test_salon_admin_role_is_admin(self):
        """Salon-Admin role is 'admin' in /auth/me response"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Check /auth/me
        me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data["role"] == "admin", f"Expected role 'admin', got '{data.get('role')}'"
        print(f"✓ Salon-Admin role verified: {data['role']}")
    
    def test_super_admin_case_insensitive_email(self):
        """Super-Admin login works with different email case"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "Bornaja23@gmail.com",  # Different case
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Case-insensitive login failed: {response.text}"
        print("✓ Super-Admin case-insensitive email login works")


class TestCategoriesPublic:
    """Test public categories endpoint"""
    
    def test_get_categories_returns_enabled_categories(self):
        """GET /api/categories returns enabled categories"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have categories with key and label
        if len(data) > 0:
            assert "key" in data[0]
            assert "label" in data[0]
        print(f"✓ GET /api/categories returned {len(data)} categories")
        return data
    
    def test_categories_have_expected_structure(self):
        """Categories have key and label fields"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        data = response.json()
        
        expected_keys = ["hair", "massage", "nails", "makeup", "depilation", "cosmetics", "eyebrows"]
        expected_labels = ["Frizura", "Masaža", "Nokti", "Šminkanje", "Depilacija", "Kozmetika", "Obrve/Trepavice"]
        
        for cat in data:
            assert cat["key"] in expected_keys, f"Unexpected category key: {cat['key']}"
            assert cat["label"] in expected_labels, f"Unexpected category label: {cat['label']}"
        print(f"✓ All categories have valid structure")


class TestCategoriesConfig:
    """Test categories config endpoint (super_admin only)"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super-admin token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return resp.json()["access_token"]
    
    @pytest.fixture
    def salon_admin_token(self):
        """Get salon-admin token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        return resp.json()["access_token"]
    
    def test_get_categories_config_super_admin(self, super_admin_token):
        """GET /api/categories/config returns all 7 categories with toggle state (super_admin only)"""
        response = requests.get(f"{BASE_URL}/api/categories/config", headers={
            "Authorization": f"Bearer {super_admin_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert len(data) == 7, f"Expected 7 categories, got {len(data)}"
        
        # Check structure
        for cat in data:
            assert "key" in cat
            assert "label" in cat
            assert "enabled" in cat
            assert isinstance(cat["enabled"], bool)
        
        print(f"✓ GET /api/categories/config returned {len(data)} categories with toggle state")
        return data
    
    def test_get_categories_config_forbidden_for_salon_admin(self, salon_admin_token):
        """GET /api/categories/config returns 403 for salon-admin"""
        response = requests.get(f"{BASE_URL}/api/categories/config", headers={
            "Authorization": f"Bearer {salon_admin_token}"
        })
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ GET /api/categories/config returns 403 for salon-admin")
    
    def test_get_categories_config_unauthorized_without_token(self):
        """GET /api/categories/config returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/categories/config")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/categories/config returns 401 without token")


class TestCategoryToggle:
    """Test category toggle functionality"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super-admin token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return resp.json()["access_token"]
    
    @pytest.fixture
    def salon_admin_token(self):
        """Get salon-admin token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        return resp.json()["access_token"]
    
    def test_toggle_category_off_super_admin(self, super_admin_token):
        """PUT /api/categories/config toggles a category off (super_admin only)"""
        # First get current state
        config_resp = requests.get(f"{BASE_URL}/api/categories/config", headers={
            "Authorization": f"Bearer {super_admin_token}"
        })
        initial_config = config_resp.json()
        
        # Find a category to toggle (use 'nails' for testing)
        test_category = "nails"
        initial_state = next((c["enabled"] for c in initial_config if c["key"] == test_category), True)
        
        # Toggle off
        toggle_resp = requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": False},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert toggle_resp.status_code == 200, f"Toggle failed: {toggle_resp.text}"
        data = toggle_resp.json()
        assert data["category"] == test_category
        assert data["enabled"] == False
        print(f"✓ Category '{test_category}' toggled OFF")
        
        # Verify in config
        verify_resp = requests.get(f"{BASE_URL}/api/categories/config", headers={
            "Authorization": f"Bearer {super_admin_token}"
        })
        verify_config = verify_resp.json()
        nails_state = next((c["enabled"] for c in verify_config if c["key"] == test_category), None)
        assert nails_state == False, f"Category should be disabled, got {nails_state}"
        
        # Restore original state
        requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": initial_state},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        print(f"✓ Category '{test_category}' restored to original state")
    
    def test_toggle_category_on_super_admin(self, super_admin_token):
        """PUT /api/categories/config toggles a category on (super_admin only)"""
        test_category = "makeup"
        
        # First disable it
        requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": False},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        # Now enable it
        toggle_resp = requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": True},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert toggle_resp.status_code == 200
        data = toggle_resp.json()
        assert data["enabled"] == True
        print(f"✓ Category '{test_category}' toggled ON")
    
    def test_toggle_category_forbidden_for_salon_admin(self, salon_admin_token):
        """PUT /api/categories/config returns 403 for salon-admin"""
        response = requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": "hair", "enabled": False},
            headers={"Authorization": f"Bearer {salon_admin_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ PUT /api/categories/config returns 403 for salon-admin")
    
    def test_toggle_invalid_category(self, super_admin_token):
        """PUT /api/categories/config returns 400 for invalid category"""
        response = requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": "invalid_category", "enabled": False},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ PUT /api/categories/config returns 400 for invalid category")


class TestServiceFiltering:
    """Test that disabling a category filters services"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super-admin token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return resp.json()["access_token"]
    
    @pytest.fixture
    def salon_admin_token(self):
        """Get salon-admin token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        return resp.json()["access_token"]
    
    def test_disabled_category_hides_services_public(self, super_admin_token):
        """Disabling a category removes its services from GET /api/services (public)"""
        test_category = "nails"
        
        # Get services before disabling
        services_before = requests.get(f"{BASE_URL}/api/services").json()
        nails_services_before = [s for s in services_before if s["category"] == test_category]
        
        # Disable nails category
        requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": False},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        # Get services after disabling
        services_after = requests.get(f"{BASE_URL}/api/services").json()
        nails_services_after = [s for s in services_after if s["category"] == test_category]
        
        # Nails services should be hidden
        assert len(nails_services_after) == 0, f"Expected 0 nails services, got {len(nails_services_after)}"
        print(f"✓ Disabled category '{test_category}' hides {len(nails_services_before)} services from public")
        
        # Re-enable category
        requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": True},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        # Verify services are back
        services_restored = requests.get(f"{BASE_URL}/api/services").json()
        nails_services_restored = [s for s in services_restored if s["category"] == test_category]
        assert len(nails_services_restored) == len(nails_services_before), "Services not restored after re-enabling"
        print(f"✓ Re-enabled category '{test_category}' restores services")
    
    def test_disabled_category_hides_services_salon_admin(self, super_admin_token, salon_admin_token):
        """Disabling a category filters services for salon-admin"""
        test_category = "nails"
        
        # Get services as salon-admin before disabling
        services_before = requests.get(f"{BASE_URL}/api/services", headers={
            "Authorization": f"Bearer {salon_admin_token}"
        }).json()
        nails_services_before = [s for s in services_before if s["category"] == test_category]
        
        # Disable nails category (as super-admin)
        requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": False},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        # Get services as salon-admin after disabling
        services_after = requests.get(f"{BASE_URL}/api/services", headers={
            "Authorization": f"Bearer {salon_admin_token}"
        }).json()
        nails_services_after = [s for s in services_after if s["category"] == test_category]
        
        # Nails services should be hidden for salon-admin too
        assert len(nails_services_after) == 0, f"Expected 0 nails services for salon-admin, got {len(nails_services_after)}"
        print(f"✓ Disabled category '{test_category}' hides services from salon-admin")
        
        # Re-enable category
        requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": True},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
    
    def test_disabled_category_hides_from_public_categories(self, super_admin_token):
        """Disabling a category removes it from GET /api/categories (public)"""
        test_category = "depilation"
        
        # Get categories before
        cats_before = requests.get(f"{BASE_URL}/api/categories").json()
        has_depilation_before = any(c["key"] == test_category for c in cats_before)
        
        # Disable depilation
        requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": False},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        
        # Get categories after
        cats_after = requests.get(f"{BASE_URL}/api/categories").json()
        has_depilation_after = any(c["key"] == test_category for c in cats_after)
        
        assert has_depilation_after == False, f"Category '{test_category}' should be hidden from public"
        print(f"✓ Disabled category '{test_category}' hidden from public categories list")
        
        # Re-enable
        requests.put(f"{BASE_URL}/api/categories/config", 
            json={"category": test_category, "enabled": True},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )


class TestSuperAdminAccess:
    """Test that super-admin can access all admin endpoints"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super-admin token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        return resp.json()["access_token"]
    
    def test_super_admin_can_access_reservations(self, super_admin_token):
        """Super-Admin can access GET /api/reservations"""
        response = requests.get(f"{BASE_URL}/api/reservations", headers={
            "Authorization": f"Bearer {super_admin_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ Super-Admin can access reservations")
    
    def test_super_admin_can_access_workers(self, super_admin_token):
        """Super-Admin can access GET /api/workers"""
        response = requests.get(f"{BASE_URL}/api/workers", headers={
            "Authorization": f"Bearer {super_admin_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ Super-Admin can access workers")
    
    def test_super_admin_can_access_services(self, super_admin_token):
        """Super-Admin can access GET /api/services"""
        response = requests.get(f"{BASE_URL}/api/services", headers={
            "Authorization": f"Bearer {super_admin_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ Super-Admin can access services")
    
    def test_super_admin_can_access_blacklist(self, super_admin_token):
        """Super-Admin can access GET /api/blacklist"""
        response = requests.get(f"{BASE_URL}/api/blacklist", headers={
            "Authorization": f"Bearer {super_admin_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ Super-Admin can access blacklist")
    
    def test_super_admin_can_access_settings(self, super_admin_token):
        """Super-Admin can access GET /api/settings"""
        response = requests.get(f"{BASE_URL}/api/settings", headers={
            "Authorization": f"Bearer {super_admin_token}"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ Super-Admin can access settings")
    
    def test_super_admin_can_update_settings(self, super_admin_token):
        """Super-Admin can update settings"""
        # Get current settings
        current = requests.get(f"{BASE_URL}/api/settings", headers={
            "Authorization": f"Bearer {super_admin_token}"
        }).json()
        
        # Update settings
        response = requests.put(f"{BASE_URL}/api/settings", 
            json={"salon_name": current.get("salon_name", "Test Salon")},
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ Super-Admin can update settings")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
