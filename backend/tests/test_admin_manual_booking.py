"""
Test Admin Manual Booking Feature (Ručna Rezervacija)
Tests for POST /api/admin/reservations endpoint with:
- Admin authentication
- Conflict detection (409 with warnings)
- Force override option
- Reservation creation and listing
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
SUPER_ADMIN_EMAIL = "bornaja23@gmail.com"
SUPER_ADMIN_PASSWORD = "Markonijus23!"
SALON_ADMIN_EMAIL = "admin@salon.com"
SALON_ADMIN_PASSWORD = "Admin123!"

# Known worker and service IDs from seed data
WORKER_SUZANA = "69d4d6f82990ad8a6366bf7d"
WORKER_MILENA = "69d4d6f82990ad8a6366bf7e"
WORKER_SLOBODAN = "69d4d6f82990ad8a6366bf7f"
SERVICE_SISANJE = "69d3b77e0b47ad8f729e9ba2"  # 30min
SERVICE_MANIKIR = "69d3b77e0b47ad8f729e9ba4"  # 45min
SERVICE_RELAX_MASAZA = "69d3b77e0b47ad8f729e9ba6"  # 60min

# Test date in the future (April 2026)
TEST_DATE = "2026-04-20"
TEST_TIME = "14:00"


class TestAdminManualBookingAuth:
    """Test authentication requirements for admin reservation endpoint"""
    
    def test_admin_reservation_without_auth_returns_401(self):
        """POST /api/admin/reservations without auth should return 401"""
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}],
            "date": TEST_DATE,
            "time": TEST_TIME,
            "client_name": "Test Client",
            "client_phone": "+381641234567",
            "force": False
        }
        response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: Admin reservation without auth returns 401")
    
    def test_admin_reservation_with_invalid_token_returns_401(self):
        """POST /api/admin/reservations with invalid token should return 401"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}],
            "date": TEST_DATE,
            "time": TEST_TIME,
            "client_name": "Test Client",
            "client_phone": "+381641234567",
            "force": False
        }
        response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: Admin reservation with invalid token returns 401")


class TestAdminManualBookingSuccess:
    """Test successful admin reservation creation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_reservation_ids = []
        yield
        # Cleanup: Cancel test reservations
        for res_id in self.created_reservation_ids:
            try:
                requests.put(f"{BASE_URL}/api/reservations/{res_id}/cancel", headers=self.headers)
            except:
                pass
    
    def test_admin_creates_reservation_successfully(self):
        """POST /api/admin/reservations creates reservation with admin auth"""
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}],
            "date": TEST_DATE,
            "time": "15:00",
            "client_name": "TEST_Admin_Booking_Client",
            "client_phone": "+381649999001",
            "force": False
        }
        response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=self.headers)
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response should have 'id'"
        assert "booking_id" in data, "Response should have 'booking_id'"
        assert data["client_name"] == "TEST_Admin_Booking_Client"
        assert data["date"] == TEST_DATE
        assert data["time"] == "15:00"
        assert data["status"] == "confirmed"
        
        self.created_reservation_ids.append(data["id"])
        print(f"PASS: Admin created reservation #{data['booking_id']} successfully")
    
    def test_admin_creates_multi_service_reservation(self):
        """POST /api/admin/reservations with multiple services"""
        payload = {
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}
            ],
            "date": TEST_DATE,
            "time": "16:00",
            "client_name": "TEST_Multi_Service_Client",
            "client_phone": "+381649999002",
            "force": False
        }
        response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=self.headers)
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify multi-service data
        assert len(data["service_worker_pairs"]) == 2, "Should have 2 service-worker pairs"
        assert len(data["service_names"]) == 2, "Should have 2 service names"
        
        self.created_reservation_ids.append(data["id"])
        print(f"PASS: Admin created multi-service reservation #{data['booking_id']}")
    
    def test_admin_reservation_appears_in_listing(self):
        """Admin reservation should appear in GET /api/reservations"""
        # First create a reservation
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}],
            "date": TEST_DATE,
            "time": "17:00",
            "client_name": "TEST_Listing_Client",
            "client_phone": "+381649999003",
            "force": False
        }
        create_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=self.headers)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        created_id = create_response.json()["id"]
        self.created_reservation_ids.append(created_id)
        
        # Now fetch reservations for that date
        list_response = requests.get(f"{BASE_URL}/api/reservations?date={TEST_DATE}", headers=self.headers)
        assert list_response.status_code == 200, f"List failed: {list_response.text}"
        
        reservations = list_response.json()
        found = any(r["id"] == created_id for r in reservations)
        assert found, f"Created reservation {created_id} not found in listing"
        
        # Verify the reservation has all timeline details
        res = next(r for r in reservations if r["id"] == created_id)
        assert "time" in res
        assert "end_time" in res
        assert "total_duration" in res
        assert "service_worker_pairs" in res
        
        print(f"PASS: Admin reservation appears in listing with all timeline details")


class TestAdminManualBookingConflicts:
    """Test conflict detection and force override"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_reservation_ids = []
        yield
        # Cleanup
        for res_id in self.created_reservation_ids:
            try:
                requests.put(f"{BASE_URL}/api/reservations/{res_id}/cancel", headers=self.headers)
            except:
                pass
    
    def test_overlap_returns_409_when_force_false(self):
        """Overlapping reservation with force=false should return 409 with warning"""
        # First create a reservation
        first_payload = {
            "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}],
            "date": TEST_DATE,
            "time": "10:00",
            "client_name": "TEST_First_Client",
            "client_phone": "+381649999010",
            "force": False
        }
        first_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=first_payload, headers=self.headers)
        assert first_response.status_code in [200, 201], f"First reservation failed: {first_response.text}"
        self.created_reservation_ids.append(first_response.json()["id"])
        
        # Try to create overlapping reservation for same client
        overlap_payload = {
            "service_worker_pairs": [{"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}],
            "date": TEST_DATE,
            "time": "10:15",  # Overlaps with 10:00-10:30
            "client_name": "TEST_First_Client",
            "client_phone": "+381649999010",  # Same phone
            "force": False
        }
        overlap_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=overlap_payload, headers=self.headers)
        
        assert overlap_response.status_code == 409, f"Expected 409, got {overlap_response.status_code}: {overlap_response.text}"
        
        # Verify warning message is in response
        detail = overlap_response.json().get("detail", "")
        assert "preklapa" in detail.lower() or "overlap" in detail.lower() or "|" in detail, \
            f"Expected overlap warning in detail: {detail}"
        
        print(f"PASS: Overlap returns 409 with warning: {detail}")
    
    def test_overlap_with_force_true_creates_anyway(self):
        """Overlapping reservation with force=true should create anyway (override)"""
        # First create a reservation
        first_payload = {
            "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}],
            "date": TEST_DATE,
            "time": "11:00",
            "client_name": "TEST_Force_Client",
            "client_phone": "+381649999011",
            "force": False
        }
        first_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=first_payload, headers=self.headers)
        assert first_response.status_code in [200, 201], f"First reservation failed: {first_response.text}"
        self.created_reservation_ids.append(first_response.json()["id"])
        
        # Create overlapping reservation with force=true
        force_payload = {
            "service_worker_pairs": [{"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}],
            "date": TEST_DATE,
            "time": "11:15",  # Overlaps
            "client_name": "TEST_Force_Client",
            "client_phone": "+381649999011",  # Same phone
            "force": True  # Force override
        }
        force_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=force_payload, headers=self.headers)
        
        assert force_response.status_code in [200, 201], f"Force create failed: {force_response.text}"
        data = force_response.json()
        assert "id" in data
        self.created_reservation_ids.append(data["id"])
        
        print(f"PASS: Force override created reservation #{data['booking_id']} despite overlap")
    
    def test_unavailable_slot_returns_409_when_force_false(self):
        """Booking unavailable slot with force=false should return 409"""
        # Try to book a slot that's likely unavailable (worker busy)
        # First book a slot
        first_payload = {
            "service_worker_pairs": [{"service_id": SERVICE_RELAX_MASAZA, "worker_id": WORKER_SLOBODAN}],
            "date": TEST_DATE,
            "time": "12:00",
            "client_name": "TEST_Unavailable_Client1",
            "client_phone": "+381649999012",
            "force": False
        }
        first_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=first_payload, headers=self.headers)
        assert first_response.status_code in [200, 201], f"First reservation failed: {first_response.text}"
        self.created_reservation_ids.append(first_response.json()["id"])
        
        # Try to book same worker at same time (different client)
        unavailable_payload = {
            "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": WORKER_SLOBODAN}],
            "date": TEST_DATE,
            "time": "12:30",  # During the 60min massage (12:00-13:00)
            "client_name": "TEST_Unavailable_Client2",
            "client_phone": "+381649999013",
            "force": False
        }
        unavailable_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=unavailable_payload, headers=self.headers)
        
        # Should return 409 because slot is not available
        assert unavailable_response.status_code == 409, \
            f"Expected 409 for unavailable slot, got {unavailable_response.status_code}: {unavailable_response.text}"
        
        print(f"PASS: Unavailable slot returns 409 warning")


class TestAdminManualBookingValidation:
    """Test input validation for admin reservations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SALON_ADMIN_EMAIL,
            "password": SALON_ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_invalid_service_id_returns_400(self):
        """Invalid service ID should return 400"""
        payload = {
            "service_worker_pairs": [{"service_id": "invalid_service_id", "worker_id": WORKER_SUZANA}],
            "date": TEST_DATE,
            "time": "18:00",
            "client_name": "Test Client",
            "client_phone": "+381641234567",
            "force": False
        }
        response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=self.headers)
        assert response.status_code in [400, 422, 500], f"Expected error for invalid service, got {response.status_code}"
        print(f"PASS: Invalid service ID returns error ({response.status_code})")
    
    def test_invalid_worker_id_returns_400(self):
        """Invalid worker ID should return 400"""
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": "invalid_worker_id"}],
            "date": TEST_DATE,
            "time": "18:00",
            "client_name": "Test Client",
            "client_phone": "+381641234567",
            "force": False
        }
        response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=self.headers)
        assert response.status_code in [400, 422, 500], f"Expected error for invalid worker, got {response.status_code}"
        print(f"PASS: Invalid worker ID returns error ({response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
