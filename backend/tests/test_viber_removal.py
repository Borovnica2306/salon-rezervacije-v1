"""
Test Viber Bot API Removal and viber_phone Settings
Tests for iteration 29: Viber Bot API removed, replaced with direct viber://chat link
"""
import pytest
import requests
import os
import inspect

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestViberBotAPIRemoval:
    """Verify Viber Bot API is completely removed from backend"""
    
    def test_no_httpx_import_in_logic(self):
        """Verify httpx is not imported in logic.py"""
        logic_path = "/app/backend/logic.py"
        with open(logic_path, 'r') as f:
            content = f.read()
        
        assert "import httpx" not in content, "httpx should not be imported in logic.py"
        assert "from httpx" not in content, "httpx should not be imported in logic.py"
        print("PASS: No httpx import in logic.py")
    
    def test_no_viber_bot_functions_in_logic(self):
        """Verify Viber Bot API functions are removed from logic.py"""
        logic_path = "/app/backend/logic.py"
        with open(logic_path, 'r') as f:
            content = f.read()
        
        # These functions should NOT exist
        assert "send_viber_message" not in content, "send_viber_message function should be removed"
        assert "viber_bot_uri" not in content, "viber_bot_uri should not be referenced"
        assert "viber_token" not in content, "viber_token should not be referenced"
        assert "httpx.AsyncClient" not in content, "httpx.AsyncClient should not be used"
        print("PASS: No Viber Bot API functions in logic.py")
    
    def test_process_daily_reminders_returns_summary_only(self):
        """Verify process_daily_reminders returns summary counts, not sent counts"""
        logic_path = "/app/backend/logic.py"
        with open(logic_path, 'r') as f:
            content = f.read()
        
        # Should NOT have sent_confirmed/sent_pending in return
        assert "sent_confirmed" not in content, "sent_confirmed should not be in process_daily_reminders"
        assert "sent_pending" not in content, "sent_pending should not be in process_daily_reminders"
        
        # Should have confirmed/pending counts
        assert "confirmed_count" in content or '"confirmed"' in content, "Should have confirmed count"
        assert "pending_count" in content or '"pending"' in content, "Should have pending count"
        print("PASS: process_daily_reminders returns summary counts only")


class TestSettingsViberPhone:
    """Test Settings model has viber_phone instead of viber_token/viber_bot_uri"""
    
    def test_settings_model_has_viber_phone(self):
        """Verify SettingsUpdate and SettingsResponse have viber_phone field"""
        models_path = "/app/backend/models.py"
        with open(models_path, 'r') as f:
            content = f.read()
        
        assert "viber_phone" in content, "viber_phone should be in models.py"
        assert "viber_token" not in content, "viber_token should NOT be in models.py"
        assert "viber_bot_uri" not in content, "viber_bot_uri should NOT be in models.py"
        print("PASS: Settings model has viber_phone, not viber_token/viber_bot_uri")
    
    def test_get_settings_returns_viber_phone(self, auth_headers):
        """GET /api/settings should return viber_phone field"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "viber_phone" in data, "viber_phone should be in settings response"
        assert "viber_token" not in data, "viber_token should NOT be in settings response"
        assert "viber_bot_uri" not in data, "viber_bot_uri should NOT be in settings response"
        print(f"PASS: GET /api/settings returns viber_phone: {data.get('viber_phone')}")
    
    def test_put_settings_accepts_viber_phone(self, auth_headers):
        """PUT /api/settings should accept and save viber_phone"""
        test_phone = "381692422596"
        
        response = requests.put(f"{BASE_URL}/api/settings", 
            json={"viber_phone": test_phone},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("viber_phone") == test_phone, f"Expected viber_phone={test_phone}, got {data.get('viber_phone')}"
        print(f"PASS: PUT /api/settings accepts viber_phone: {test_phone}")
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        get_data = get_response.json()
        assert get_data.get("viber_phone") == test_phone, "viber_phone should persist after PUT"
        print("PASS: viber_phone persisted correctly")


class TestTriggerRemindersEndpoint:
    """Test trigger-reminders endpoint returns summary counts"""
    
    def test_trigger_reminders_returns_summary(self, auth_headers):
        """POST /api/admin/reservations/trigger-reminders should return summary counts"""
        response = requests.post(f"{BASE_URL}/api/admin/reservations/trigger-reminders", 
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Should have these fields
        assert "date" in data, "Response should have 'date' field"
        assert "total_reservations" in data, "Response should have 'total_reservations' field"
        assert "confirmed" in data, "Response should have 'confirmed' field"
        assert "pending" in data, "Response should have 'pending' field"
        
        # Should NOT have these fields (old Viber Bot API response)
        assert "sent_confirmed" not in data, "Response should NOT have 'sent_confirmed' field"
        assert "sent_pending" not in data, "Response should NOT have 'sent_pending' field"
        assert "errors" not in data, "Response should NOT have 'errors' field"
        
        print(f"PASS: trigger-reminders returns summary: date={data['date']}, total={data['total_reservations']}, confirmed={data['confirmed']}, pending={data['pending']}")


class TestViberPhoneInDB:
    """Test viber_phone is correctly stored in database"""
    
    def test_viber_phone_value_in_settings(self, auth_headers):
        """Verify viber_phone is set to expected value (381692422596)"""
        response = requests.get(f"{BASE_URL}/api/settings", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        viber_phone = data.get("viber_phone", "")
        
        # According to agent context, viber_phone should be 381692422596
        assert viber_phone == "381692422596", f"Expected viber_phone=381692422596, got {viber_phone}"
        print(f"PASS: viber_phone in DB is correctly set to {viber_phone}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
