"""
Test cases for client_email field in reservations
- POST /api/reservations: client_email required, stored lowercase
- GET /api/reservations: returns client_email (empty string for old reservations)
- POST /api/reservations: returns 422 if client_email missing
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_SERVICE_ID = "69d549f035e38a4c2c9f0226"
TEST_WORKER_ID = "69d54b0635e38a4c2c9f022e"


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_token(api_client):
    """Get authentication token for admin"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@salon.com",
        "password": "Admin123!"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


def get_future_date():
    """Get a date 7 days in the future"""
    return (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")


class TestEmailFieldInReservations:
    """Test client_email field in reservation endpoints"""

    def test_create_reservation_with_valid_email(self, api_client):
        """POST /api/reservations: Accepts client_email field and returns it in response"""
        future_date = get_future_date()
        
        # First get available slots
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date
        })
        
        if slots_response.status_code != 200:
            pytest.skip(f"Could not get available slots: {slots_response.text}")
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots for testing")
        
        test_time = slots[0]
        test_email = "TEST_User@Example.COM"  # Mixed case to test lowercase conversion
        
        # Create reservation with email
        response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date,
            "time": test_time,
            "client_name": "TEST_Email User",
            "client_phone": "+381641234567",
            "client_email": test_email
        })
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "client_email" in data, "Response should contain client_email field"
        assert data["client_email"] == test_email.strip().lower(), f"Email should be stored lowercase, got: {data['client_email']}"
        assert data["client_email"] == "test_user@example.com", "Email should be lowercase"
        
        # Store reservation ID for cleanup
        reservation_id = data.get("id")
        print(f"Created reservation {reservation_id} with email {data['client_email']}")
        
        return reservation_id

    def test_create_reservation_without_email_returns_422(self, api_client):
        """POST /api/reservations: Returns 422 if client_email is missing"""
        future_date = get_future_date()
        
        # First get available slots
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date
        })
        
        if slots_response.status_code != 200:
            pytest.skip(f"Could not get available slots: {slots_response.text}")
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots for testing")
        
        test_time = slots[0]
        
        # Create reservation WITHOUT email
        response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date,
            "time": test_time,
            "client_name": "TEST_No Email User",
            "client_phone": "+381641234568"
            # client_email intentionally omitted
        })
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422, f"Expected 422 for missing email, got {response.status_code}: {response.text}"
        print(f"Correctly returned 422 for missing email: {response.text}")

    def test_get_reservations_returns_email_field(self, authenticated_client):
        """GET /api/reservations: Returns client_email field (empty string for old reservations)"""
        response = authenticated_client.get(f"{BASE_URL}/api/reservations")
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Check that all reservations have client_email field
        for reservation in data:
            assert "client_email" in reservation, f"Reservation {reservation.get('id')} missing client_email field"
            # client_email should be string (empty string for old reservations)
            assert isinstance(reservation["client_email"], str), f"client_email should be string, got {type(reservation['client_email'])}"
        
        print(f"Verified {len(data)} reservations all have client_email field")

    def test_email_stored_lowercase(self, api_client):
        """POST /api/reservations: Email is stored as lowercase"""
        future_date = get_future_date()
        
        # Get available slots
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date
        })
        
        if slots_response.status_code != 200:
            pytest.skip(f"Could not get available slots: {slots_response.text}")
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots for testing")
        
        # Use a slot that's different from previous test
        test_time = slots[-1] if len(slots) > 1 else slots[0]
        
        # Test with uppercase email
        uppercase_email = "UPPERCASE@TEST.COM"
        
        response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date,
            "time": test_time,
            "client_name": "TEST_Uppercase Email",
            "client_phone": "+381641234569",
            "client_email": uppercase_email
        })
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data["client_email"] == uppercase_email.lower(), f"Email should be lowercase: {data['client_email']}"
        print(f"Email correctly stored as lowercase: {data['client_email']}")

    def test_email_with_whitespace_trimmed(self, api_client):
        """POST /api/reservations: Email whitespace is trimmed"""
        future_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")  # Different date
        
        # Get available slots
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date
        })
        
        if slots_response.status_code != 200:
            pytest.skip(f"Could not get available slots: {slots_response.text}")
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots for testing")
        
        test_time = slots[0]
        
        # Test with whitespace around email
        email_with_spaces = "  whitespace@test.com  "
        
        response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date,
            "time": test_time,
            "client_name": "TEST_Whitespace Email",
            "client_phone": "+381641234570",
            "client_email": email_with_spaces
        })
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data["client_email"] == email_with_spaces.strip().lower(), f"Email should be trimmed: {data['client_email']}"
        assert data["client_email"] == "whitespace@test.com", "Email should be trimmed and lowercase"
        print(f"Email correctly trimmed: {data['client_email']}")


class TestAdminReservationNoEmail:
    """Test that AdminReservationCreate does NOT require email (intentional)"""

    def test_admin_reservation_without_email_succeeds(self, authenticated_client):
        """POST /api/admin/reservations: Does NOT require client_email (intentional)"""
        future_date = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")
        
        # Get available slots
        slots_response = authenticated_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date
        })
        
        if slots_response.status_code != 200:
            pytest.skip(f"Could not get available slots: {slots_response.text}")
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots for testing")
        
        test_time = slots[0]
        
        # Admin reservation WITHOUT email (should succeed)
        response = authenticated_client.post(f"{BASE_URL}/api/admin/reservations", json={
            "service_worker_pairs": [{"service_id": TEST_SERVICE_ID, "worker_id": TEST_WORKER_ID}],
            "date": future_date,
            "time": test_time,
            "client_name": "TEST_Admin Booking",
            "client_phone": "+381641234571",
            "force": False
            # client_email intentionally omitted - admin bookings don't require it
        })
        
        # Should succeed (admin bookings don't require email)
        assert response.status_code in [200, 409], f"Expected 200 or 409, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            # Admin reservation should have empty client_email
            assert data.get("client_email", "") == "", "Admin reservation should have empty client_email"
            print(f"Admin reservation created without email: {data.get('id')}")
        else:
            print(f"Admin reservation returned 409 (conflict): {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
