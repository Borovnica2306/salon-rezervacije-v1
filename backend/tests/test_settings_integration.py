"""
Test Settings API - SMTP and Viber credential management
Tests for iteration 26: Settings API extended with smtp_server, smtp_port, smtp_user, smtp_password, viber_token, viber_bot_uri fields
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"


class TestSettingsAPI:
    """Test Settings API with SMTP and Viber fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_settings_returns_smtp_fields(self):
        """GET /api/settings returns smtp_server, smtp_port, smtp_user, smtp_password fields"""
        response = self.session.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        
        data = response.json()
        # Verify SMTP fields exist
        assert "smtp_server" in data, "smtp_server field missing"
        assert "smtp_port" in data, "smtp_port field missing"
        assert "smtp_user" in data, "smtp_user field missing"
        assert "smtp_password" in data, "smtp_password field missing"
        
        # Verify default values
        assert data["smtp_server"] == "smtp.gmail.com", f"Expected default smtp_server 'smtp.gmail.com', got '{data['smtp_server']}'"
        assert data["smtp_port"] == 587, f"Expected default smtp_port 587, got {data['smtp_port']}"
        
        print(f"✓ GET /api/settings returns SMTP fields with defaults: server={data['smtp_server']}, port={data['smtp_port']}")
    
    def test_get_settings_returns_viber_fields(self):
        """GET /api/settings returns viber_token, viber_bot_uri fields"""
        response = self.session.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        
        data = response.json()
        # Verify Viber fields exist
        assert "viber_token" in data, "viber_token field missing"
        assert "viber_bot_uri" in data, "viber_bot_uri field missing"
        
        print(f"✓ GET /api/settings returns Viber fields: token='{data['viber_token']}', uri='{data['viber_bot_uri']}'")
    
    def test_put_settings_accepts_smtp_fields(self):
        """PUT /api/settings accepts and persists SMTP fields"""
        # Update with test SMTP values
        test_smtp_data = {
            "smtp_server": "test.smtp.server.com",
            "smtp_port": 465,
            "smtp_user": "test@example.com",
            "smtp_password": "test_password_123"
        }
        
        response = self.session.put(f"{BASE_URL}/api/settings", json=test_smtp_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["smtp_server"] == test_smtp_data["smtp_server"]
        assert data["smtp_port"] == test_smtp_data["smtp_port"]
        assert data["smtp_user"] == test_smtp_data["smtp_user"]
        assert data["smtp_password"] == test_smtp_data["smtp_password"]
        
        print(f"✓ PUT /api/settings accepts SMTP fields")
        
        # Verify persistence with GET
        get_response = self.session.get(f"{BASE_URL}/api/settings")
        assert get_response.status_code == 200
        
        get_data = get_response.json()
        assert get_data["smtp_server"] == test_smtp_data["smtp_server"]
        assert get_data["smtp_port"] == test_smtp_data["smtp_port"]
        assert get_data["smtp_user"] == test_smtp_data["smtp_user"]
        assert get_data["smtp_password"] == test_smtp_data["smtp_password"]
        
        print(f"✓ SMTP fields persisted correctly across GET requests")
        
        # Reset to defaults
        self.session.put(f"{BASE_URL}/api/settings", json={
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_password": ""
        })
    
    def test_put_settings_accepts_viber_fields(self):
        """PUT /api/settings accepts and persists Viber fields"""
        # Update with test Viber values
        test_viber_data = {
            "viber_token": "test_viber_token_abc123",
            "viber_bot_uri": "testbotname"
        }
        
        response = self.session.put(f"{BASE_URL}/api/settings", json=test_viber_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["viber_token"] == test_viber_data["viber_token"]
        assert data["viber_bot_uri"] == test_viber_data["viber_bot_uri"]
        
        print(f"✓ PUT /api/settings accepts Viber fields")
        
        # Verify persistence with GET
        get_response = self.session.get(f"{BASE_URL}/api/settings")
        assert get_response.status_code == 200
        
        get_data = get_response.json()
        assert get_data["viber_token"] == test_viber_data["viber_token"]
        assert get_data["viber_bot_uri"] == test_viber_data["viber_bot_uri"]
        
        print(f"✓ Viber fields persisted correctly across GET requests")
        
        # Reset to defaults
        self.session.put(f"{BASE_URL}/api/settings", json={
            "viber_token": "",
            "viber_bot_uri": ""
        })
    
    def test_put_settings_requires_admin_auth(self):
        """PUT /api/settings requires admin authentication"""
        # Create unauthenticated session
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.put(f"{BASE_URL}/api/settings", json={
            "smtp_server": "unauthorized.server.com"
        })
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated request, got {response.status_code}"
        
        print(f"✓ PUT /api/settings requires admin auth (returned {response.status_code})")
    
    def test_settings_all_fields_persist_together(self):
        """Test that all SMTP and Viber fields can be saved together and persist"""
        # Save all integration fields together
        all_fields = {
            "smtp_server": "combined.smtp.test.com",
            "smtp_port": 2525,
            "smtp_user": "combined@test.com",
            "smtp_password": "combined_pass_456",
            "viber_token": "combined_viber_token_xyz",
            "viber_bot_uri": "combinedbot"
        }
        
        response = self.session.put(f"{BASE_URL}/api/settings", json=all_fields)
        assert response.status_code == 200
        
        # Verify all fields in response
        data = response.json()
        for key, value in all_fields.items():
            assert data[key] == value, f"Field {key} mismatch: expected {value}, got {data[key]}"
        
        print(f"✓ All integration fields saved together")
        
        # Verify persistence
        get_response = self.session.get(f"{BASE_URL}/api/settings")
        assert get_response.status_code == 200
        
        get_data = get_response.json()
        for key, value in all_fields.items():
            assert get_data[key] == value, f"Field {key} not persisted: expected {value}, got {get_data[key]}"
        
        print(f"✓ All integration fields persisted correctly")
        
        # Reset to defaults
        self.session.put(f"{BASE_URL}/api/settings", json={
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_password": "",
            "viber_token": "",
            "viber_bot_uri": ""
        })
    
    def test_smtp_port_is_integer(self):
        """Test that smtp_port is returned as integer"""
        response = self.session.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["smtp_port"], int), f"smtp_port should be int, got {type(data['smtp_port'])}"
        
        print(f"✓ smtp_port is integer type: {data['smtp_port']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
