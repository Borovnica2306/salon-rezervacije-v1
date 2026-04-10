"""
Backend API Tests - Refactoring Verification
Tests all endpoints after code split from monolithic server.py into 6 modular files:
- server.py (app init)
- database.py (MongoDB)
- models.py (Pydantic)
- auth.py (JWT)
- logic.py (Smart Pairing + Viber placeholder)
- routes.py (all endpoints)

All functionality must remain identical - zero behavior changes.
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://slot-reserve-23.preview.emergentagent.com').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "bornaja23@gmail.com"
SUPER_ADMIN_PASSWORD = "Markonijus23!"
SALON_ADMIN_EMAIL = "admin@salon.com"
SALON_ADMIN_PASSWORD = "Admin123!"

# Test service/worker IDs from context
TEST_SERVICE_SISANJE = "69d3b77e0b47ad8f729e9ba2"  # 30min
TEST_SERVICE_MANIKIR = "69d3b77e0b47ad8f729e9ba4"  # 45min
TEST_WORKER_SUZANA = "69d4d6f82990ad8a6366bf7d"
TEST_WORKER_MILENA = "69d4d6f82990ad8a6366bf7e"


class TestAuthEndpoints:
    """Test authentication endpoints after refactoring"""
    
    def test_super_admin_login(self):
        """POST /api/auth/login works with super-admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain 'access_token'"
        assert data["role"] == "super_admin", f"Expected role 'super_admin', got {data.get('role')}"
        assert data["email"] == SUPER_ADMIN_EMAIL
        print(f"SUCCESS: Super-admin login works, role={data['role']}")
    
    def test_salon_admin_login(self):
        """POST /api/auth/login works with salon-admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain 'access_token'"
        assert data["role"] == "admin", f"Expected role 'admin', got {data.get('role')}"
        assert data["email"] == SALON_ADMIN_EMAIL
        print(f"SUCCESS: Salon-admin login works, role={data['role']}")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login returns 401 for invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Invalid credentials return 401")
    
    def test_auth_me_with_token(self):
        """GET /api/auth/me returns user info with valid token"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Then get /me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["email"] == SALON_ADMIN_EMAIL
        assert "id" in data
        print(f"SUCCESS: /auth/me returns user info: {data['email']}")
    
    def test_auth_me_without_token(self):
        """GET /api/auth/me returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: /auth/me without token returns 401")


class TestPublicEndpoints:
    """Test public endpoints (no auth required)"""
    
    def test_get_categories(self):
        """GET /api/categories returns enabled categories"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one category"
        
        # Check structure
        for cat in data:
            assert "key" in cat, "Category should have 'key'"
            assert "label" in cat, "Category should have 'label'"
        
        print(f"SUCCESS: GET /api/categories returns {len(data)} categories")
    
    def test_get_services(self):
        """GET /api/services returns active services"""
        response = requests.get(f"{BASE_URL}/api/services")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Check structure
        for service in data:
            assert "id" in service
            assert "name" in service
            assert "category" in service
            assert "duration" in service
            assert "price" in service
            assert "active" in service
        
        print(f"SUCCESS: GET /api/services returns {len(data)} services")
    
    def test_get_workers(self):
        """GET /api/workers returns active workers"""
        response = requests.get(f"{BASE_URL}/api/workers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Check structure
        for worker in data:
            assert "id" in worker
            assert "name" in worker
            assert "services" in worker
            assert "work_start" in worker
            assert "work_end" in worker
        
        print(f"SUCCESS: GET /api/workers returns {len(data)} workers")
    
    def test_get_settings(self):
        """GET /api/settings returns salon settings"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "salon_name" in data
        assert "work_start" in data
        assert "work_end" in data
        
        print(f"SUCCESS: GET /api/settings returns salon_name={data['salon_name']}")


class TestSmartPairingLogic:
    """Test Smart Pairing logic (15-min Social Buffer)"""
    
    def test_available_slots_single_service(self):
        """POST /api/reservations/available-slots with 1 service returns slots"""
        # Use a future date
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "slots" in data
        assert isinstance(data["slots"], list)
        
        print(f"SUCCESS: Single service returns {len(data['slots'])} slots for {future_date}")
    
    def test_available_slots_two_services_with_buffer(self):
        """POST /api/reservations/available-slots with 2 services returns 15-min Social Buffer"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA},
                {"service_id": TEST_SERVICE_MANIKIR, "worker_id": TEST_WORKER_MILENA}
            ],
            "date": future_date
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "slots" in data
        assert "slot_details" in data
        
        # Check that slot_details contain gap information
        if data["slots"]:
            first_slot = data["slots"][0]
            slot_detail = data["slot_details"].get(first_slot, {})
            
            # With 2 services, gap should be 15 minutes
            gap_minutes = slot_detail.get("gap_minutes", 0)
            assert gap_minutes == 15, f"Expected 15-min gap for 2 services, got {gap_minutes}"
            
            print(f"SUCCESS: 2 services return {len(data['slots'])} slots with {gap_minutes}-min buffer")
        else:
            print("WARNING: No slots available for the test date")


class TestReservationFlow:
    """Test reservation creation and management"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_create_reservation(self, admin_token):
        """POST /api/reservations creates reservation successfully"""
        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        test_phone = f"+381641234{datetime.now().strftime('%H%M%S')}"  # Unique phone
        
        # First get available slots
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date
        })
        
        if slots_response.status_code != 200 or not slots_response.json().get("slots"):
            pytest.skip("No slots available for test date")
        
        available_slot = slots_response.json()["slots"][0]
        
        # Create reservation
        response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date,
            "time": available_slot,
            "client_name": "TEST_RefactorTest",
            "client_phone": test_phone
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "booking_id" in data
        assert data["status"] == "confirmed"
        
        reservation_id = data["id"]
        print(f"SUCCESS: Reservation created with ID={reservation_id}, booking_id={data['booking_id']}")
        
        # Cleanup: Cancel the reservation
        cancel_response = requests.put(
            f"{BASE_URL}/api/reservations/{reservation_id}/cancel",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert cancel_response.status_code == 200, f"Cleanup failed: {cancel_response.text}"
        print(f"SUCCESS: Test reservation cancelled")
    
    def test_anti_conflict_same_phone_overlap(self, admin_token):
        """Anti-Conflict: overlapping reservation with same phone returns 409"""
        future_date = (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d")
        test_phone = "+381641111111"
        
        # Get available slots
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date
        })
        
        if slots_response.status_code != 200 or not slots_response.json().get("slots"):
            pytest.skip("No slots available for test date")
        
        available_slot = slots_response.json()["slots"][0]
        
        # Create first reservation
        first_response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date,
            "time": available_slot,
            "client_name": "TEST_AntiConflict1",
            "client_phone": test_phone
        })
        
        if first_response.status_code != 200:
            pytest.skip(f"Could not create first reservation: {first_response.text}")
        
        first_id = first_response.json()["id"]
        
        try:
            # Try to create overlapping reservation with SAME phone
            second_response = requests.post(f"{BASE_URL}/api/reservations", json={
                "service_worker_pairs": [
                    {"service_id": TEST_SERVICE_MANIKIR, "worker_id": TEST_WORKER_MILENA}
                ],
                "date": future_date,
                "time": available_slot,  # Same time = overlap
                "client_name": "TEST_AntiConflict2",
                "client_phone": test_phone  # Same phone
            })
            
            assert second_response.status_code == 409, f"Expected 409 for overlap, got {second_response.status_code}: {second_response.text}"
            print("SUCCESS: Anti-Conflict returns 409 for same phone overlapping reservation")
            
        finally:
            # Cleanup
            requests.put(
                f"{BASE_URL}/api/reservations/{first_id}/cancel",
                headers={"Authorization": f"Bearer {admin_token}"}
            )


class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_reservations_admin(self, admin_token):
        """GET /api/reservations (admin) returns reservation list"""
        response = requests.get(
            f"{BASE_URL}/api/reservations",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: GET /api/reservations returns {len(data)} reservations")
    
    def test_get_reservations_without_auth(self):
        """GET /api/reservations without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/reservations")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: GET /api/reservations without auth returns 401")
    
    def test_get_blacklist_admin(self, admin_token):
        """GET /api/blacklist (admin) returns blacklist"""
        response = requests.get(
            f"{BASE_URL}/api/blacklist",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: GET /api/blacklist returns {len(data)} entries")
    
    def test_get_blacklist_without_auth(self):
        """GET /api/blacklist without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/blacklist")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: GET /api/blacklist without auth returns 401")


class TestClientReservations:
    """Test client reservation lookup"""
    
    def test_my_reservations_by_phone(self):
        """POST /api/my-reservations returns client reservations by phone"""
        response = requests.post(f"{BASE_URL}/api/my-reservations", json={
            "phone": "+381641234567"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: POST /api/my-reservations returns {len(data)} reservations")


class TestPaymentStatusToggle:
    """Test payment status toggle endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_toggle_payment_status(self, admin_token):
        """PUT /api/reservations/{id}/payment-status toggles payment"""
        future_date = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
        test_phone = f"+381642222{datetime.now().strftime('%H%M%S')}"
        
        # Get available slots
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date
        })
        
        if slots_response.status_code != 200 or not slots_response.json().get("slots"):
            pytest.skip("No slots available for test date")
        
        available_slot = slots_response.json()["slots"][0]
        
        # Create reservation
        create_response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date,
            "time": available_slot,
            "client_name": "TEST_PaymentToggle",
            "client_phone": test_phone
        })
        
        if create_response.status_code != 200:
            pytest.skip(f"Could not create reservation: {create_response.text}")
        
        reservation_id = create_response.json()["id"]
        initial_status = create_response.json()["payment_status"]
        
        try:
            # Toggle payment status
            toggle_response = requests.put(
                f"{BASE_URL}/api/reservations/{reservation_id}/payment-status",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert toggle_response.status_code == 200, f"Expected 200, got {toggle_response.status_code}: {toggle_response.text}"
            
            new_status = toggle_response.json()["payment_status"]
            expected_status = "paid" if initial_status == "pending" else "pending"
            assert new_status == expected_status, f"Expected {expected_status}, got {new_status}"
            
            print(f"SUCCESS: Payment status toggled from {initial_status} to {new_status}")
            
        finally:
            # Cleanup
            requests.put(
                f"{BASE_URL}/api/reservations/{reservation_id}/cancel",
                headers={"Authorization": f"Bearer {admin_token}"}
            )


class TestCancelReservation:
    """Test reservation cancellation"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_cancel_reservation_admin(self, admin_token):
        """PUT /api/reservations/{id}/cancel cancels reservation"""
        future_date = (datetime.now() + timedelta(days=13)).strftime("%Y-%m-%d")
        test_phone = f"+381643333{datetime.now().strftime('%H%M%S')}"
        
        # Get available slots
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date
        })
        
        if slots_response.status_code != 200 or not slots_response.json().get("slots"):
            pytest.skip("No slots available for test date")
        
        available_slot = slots_response.json()["slots"][0]
        
        # Create reservation
        create_response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": TEST_SERVICE_SISANJE, "worker_id": TEST_WORKER_SUZANA}
            ],
            "date": future_date,
            "time": available_slot,
            "client_name": "TEST_CancelTest",
            "client_phone": test_phone
        })
        
        if create_response.status_code != 200:
            pytest.skip(f"Could not create reservation: {create_response.text}")
        
        reservation_id = create_response.json()["id"]
        
        # Cancel reservation
        cancel_response = requests.put(
            f"{BASE_URL}/api/reservations/{reservation_id}/cancel",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert cancel_response.status_code == 200, f"Expected 200, got {cancel_response.status_code}: {cancel_response.text}"
        print(f"SUCCESS: Reservation {reservation_id} cancelled successfully")
    
    def test_cancel_without_auth(self):
        """PUT /api/reservations/{id}/cancel without auth returns 401"""
        response = requests.put(f"{BASE_URL}/api/reservations/fake-id/cancel")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Cancel without auth returns 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
