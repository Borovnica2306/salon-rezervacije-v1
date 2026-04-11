"""
Test suite for Timeline Grid Refactor - Admin Dashboard
Tests: Core APIs, Admin reservation creation, Boundary checks, Anti-conflict logic
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"

# Known IDs from seed data
WORKER_SUZANA = "69d4d6f82990ad8a6366bf7d"
WORKER_MILENA = "69d4d6f82990ad8a6366bf7e"
WORKER_SLOBODAN = "69d4d6f82990ad8a6366bf7f"
SERVICE_SISANJE = "69d3b77e0b47ad8f729e9ba2"  # 30min
SERVICE_MANIKIR = "69d3b77e0b47ad8f729e9ba4"  # 45min
SERVICE_RELAX_MASAZA = "69d3b77e0b47ad8f729e9ba6"  # 60min


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture
def auth_headers(admin_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_date():
    """Get a future date for testing (skip Sundays)"""
    date = datetime.now() + timedelta(days=3)
    # Skip Sunday (day 6)
    while date.weekday() == 6:
        date += timedelta(days=1)
    return date.strftime("%Y-%m-%d")


class TestCoreAPIs:
    """Test that all core APIs still work after refactor"""
    
    def test_get_services(self):
        """GET /api/services returns list of services"""
        response = requests.get(f"{BASE_URL}/api/services")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of services"
        assert len(data) > 0, "Expected at least one service"
        # Verify service structure
        service = data[0]
        assert "id" in service
        assert "name" in service
        assert "duration" in service
        assert "price" in service
        print(f"SUCCESS: GET /api/services returned {len(data)} services")
    
    def test_get_workers(self):
        """GET /api/workers returns list of workers"""
        response = requests.get(f"{BASE_URL}/api/workers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of workers"
        assert len(data) > 0, "Expected at least one worker"
        # Verify worker structure
        worker = data[0]
        assert "id" in worker
        assert "name" in worker
        assert "work_start" in worker
        assert "work_end" in worker
        print(f"SUCCESS: GET /api/workers returned {len(data)} workers")
        # Check for known workers
        worker_names = [w["name"] for w in data]
        assert "Suzana" in worker_names or any("Suzana" in n for n in worker_names), "Expected Suzana in workers"
    
    def test_get_settings(self):
        """GET /api/settings returns salon settings"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "work_start" in data
        assert "work_end" in data
        print(f"SUCCESS: GET /api/settings - work hours: {data['work_start']} - {data['work_end']}")
    
    def test_auth_login(self):
        """POST /api/auth/login works with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "access_token" in data
        assert "email" in data
        assert data["email"] == ADMIN_EMAIL
        print(f"SUCCESS: POST /api/auth/login - logged in as {data['email']}")
    
    def test_get_reservations_requires_auth(self):
        """GET /api/reservations requires authentication"""
        response = requests.get(f"{BASE_URL}/api/reservations")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("SUCCESS: GET /api/reservations correctly requires auth")
    
    def test_get_reservations_with_auth(self, auth_headers, test_date):
        """GET /api/reservations works with auth"""
        response = requests.get(
            f"{BASE_URL}/api/reservations",
            params={"date": test_date},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list of reservations"
        print(f"SUCCESS: GET /api/reservations returned {len(data)} reservations for {test_date}")


class TestAdminReservationCreation:
    """Test POST /api/admin/reservations creates reservation correctly"""
    
    def test_admin_create_reservation(self, auth_headers, test_date):
        """Admin can create a reservation and it appears in GET /api/reservations"""
        # Use force=True to bypass slot availability check for testing
        payload = {
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": test_date,
            "time": "09:30",
            "client_name": "TEST_Timeline_Grid",
            "client_phone": "+381641234567",
            "force": True  # Force create for testing
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/reservations",
            json=payload,
            headers=auth_headers
        )
        
        assert create_response.status_code in [200, 201], f"Expected 200/201, got {create_response.status_code}: {create_response.text}"
        created = create_response.json()
        
        # Verify response structure
        assert "id" in created
        assert "booking_id" in created
        assert created["client_name"] == "TEST_Timeline_Grid"
        assert created["date"] == test_date
        assert created["time"] == "09:30"
        
        reservation_id = created["id"]
        booking_id = created["booking_id"]
        print(f"SUCCESS: Created reservation {booking_id} (ID: {reservation_id})")
        
        # Verify it appears in GET /api/reservations
        get_response = requests.get(
            f"{BASE_URL}/api/reservations",
            params={"date": test_date},
            headers=auth_headers
        )
        assert get_response.status_code == 200
        reservations = get_response.json()
        
        found = any(r["id"] == reservation_id for r in reservations)
        assert found, f"Created reservation {reservation_id} not found in GET response"
        print(f"SUCCESS: Reservation {booking_id} appears in GET /api/reservations")
        
        # Cleanup - cancel the reservation
        cancel_response = requests.put(
            f"{BASE_URL}/api/reservations/{reservation_id}/cancel",
            headers=auth_headers
        )
        assert cancel_response.status_code == 200
        print(f"SUCCESS: Cleaned up test reservation {booking_id}")


class TestBoundaryCheck:
    """Test work hours boundary check (20:45 Šišanje by Suzana returns 409)"""
    
    def test_boundary_violation_returns_409(self, auth_headers, test_date):
        """Booking at 20:45 for 30min service (ends 21:15) should return 409"""
        payload = {
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": test_date,
            "time": "20:45",
            "client_name": "TEST_Boundary",
            "client_phone": "+381641234568",
            "force": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/reservations",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 409, f"Expected 409 for boundary violation, got {response.status_code}: {response.text}"
        detail = response.json().get("detail", "")
        assert "Suzana" in detail or "21:00" in detail or "radi do" in detail, f"Expected boundary message, got: {detail}"
        print(f"SUCCESS: 20:45 booking correctly returns 409 with message: {detail}")
    
    def test_boundary_exact_succeeds(self, auth_headers, test_date):
        """Booking at 20:30 for 30min service (ends exactly 21:00) should succeed"""
        payload = {
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": test_date,
            "time": "20:30",
            "client_name": "TEST_Boundary_Exact",
            "client_phone": "+381641234569",
            "force": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/reservations",
            json=payload,
            headers=auth_headers
        )
        
        # Could be 200/201 or 409 if slot not available (already booked)
        if response.status_code in [200, 201]:
            created = response.json()
            print(f"SUCCESS: 20:30 booking succeeded - ends exactly at 21:00")
            # Cleanup
            requests.put(
                f"{BASE_URL}/api/reservations/{created['id']}/cancel",
                headers=auth_headers
            )
        elif response.status_code == 409:
            detail = response.json().get("detail", "")
            # If 409, it should NOT be about boundary violation
            assert "radi do" not in detail.lower() or "21:15" in detail, f"20:30 should not have boundary violation: {detail}"
            print(f"INFO: 20:30 slot not available (possibly already booked): {detail}")
        else:
            pytest.fail(f"Unexpected status {response.status_code}: {response.text}")


class TestAntiConflict:
    """Test anti-conflict logic (overlapping phone booking returns 409)"""
    
    def test_overlapping_booking_returns_409(self, auth_headers, test_date):
        """Same phone booking overlapping times should return 409"""
        test_phone = "+381641234570"
        
        # First booking at 11:00
        payload1 = {
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": test_date,
            "time": "11:00",
            "client_name": "TEST_Conflict_1",
            "client_phone": test_phone,
            "force": False
        }
        
        response1 = requests.post(
            f"{BASE_URL}/api/admin/reservations",
            json=payload1,
            headers=auth_headers
        )
        
        if response1.status_code not in [200, 201]:
            pytest.skip(f"Could not create first reservation: {response1.text}")
        
        first_res = response1.json()
        first_id = first_res["id"]
        print(f"Created first reservation at 11:00: {first_res['booking_id']}")
        
        try:
            # Second booking at 11:15 (overlaps with 11:00-11:30)
            payload2 = {
                "service_worker_pairs": [
                    {"service_id": SERVICE_SISANJE, "worker_id": WORKER_MILENA}  # Different worker
                ],
                "date": test_date,
                "time": "11:15",
                "client_name": "TEST_Conflict_2",
                "client_phone": test_phone,  # Same phone
                "force": False
            }
            
            response2 = requests.post(
                f"{BASE_URL}/api/admin/reservations",
                json=payload2,
                headers=auth_headers
            )
            
            assert response2.status_code == 409, f"Expected 409 for overlapping booking, got {response2.status_code}: {response2.text}"
            detail = response2.json().get("detail", "")
            assert "preklapa" in detail.lower() or "overlap" in detail.lower() or "već ima" in detail.lower(), f"Expected overlap message, got: {detail}"
            print(f"SUCCESS: Overlapping booking correctly returns 409: {detail}")
            
        finally:
            # Cleanup first reservation
            requests.put(
                f"{BASE_URL}/api/reservations/{first_id}/cancel",
                headers=auth_headers
            )
            print("Cleaned up test reservation")


class TestMultiServiceReservation:
    """Test multi-service reservations with worker_time_blocks"""
    
    def test_multi_service_creates_time_blocks(self, auth_headers, test_date):
        """Multi-service reservation should have worker_time_blocks"""
        payload = {
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}
            ],
            "date": test_date,
            "time": "14:00",
            "client_name": "TEST_MultiService",
            "client_phone": "+381641234571",
            "force": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/reservations",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code not in [200, 201]:
            pytest.skip(f"Could not create multi-service reservation: {response.text}")
        
        created = response.json()
        
        # Verify worker_time_blocks exist
        assert "worker_time_blocks" in created, "Expected worker_time_blocks in response"
        blocks = created["worker_time_blocks"]
        assert len(blocks) == 2, f"Expected 2 time blocks, got {len(blocks)}"
        
        # Verify blocks have correct structure
        for block in blocks:
            assert "worker_id" in block
            assert "service_id" in block
            assert "start_time" in block
            assert "end_time" in block
        
        # Verify first block is Suzana, second is Milena
        assert blocks[0]["worker_id"] == WORKER_SUZANA
        assert blocks[1]["worker_id"] == WORKER_MILENA
        
        print(f"SUCCESS: Multi-service reservation has {len(blocks)} time blocks")
        print(f"  Block 1: {blocks[0]['start_time']}-{blocks[0]['end_time']} (Suzana)")
        print(f"  Block 2: {blocks[1]['start_time']}-{blocks[1]['end_time']} (Milena)")
        
        # Cleanup
        requests.put(
            f"{BASE_URL}/api/reservations/{created['id']}/cancel",
            headers=auth_headers
        )


class TestAvailableSlots:
    """Test available slots endpoint"""
    
    def test_available_slots_returns_slots(self, test_date):
        """POST /api/reservations/available-slots returns slots"""
        payload = {
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": test_date
        }
        
        response = requests.post(
            f"{BASE_URL}/api/reservations/available-slots",
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "slots" in data, "Expected 'slots' in response"
        assert "slot_details" in data, "Expected 'slot_details' in response"
        
        slots = data["slots"]
        assert isinstance(slots, list), "Expected slots to be a list"
        assert len(slots) > 0, "Expected at least one available slot"
        
        # Verify slot format (HH:MM)
        for slot in slots[:5]:
            assert ":" in slot, f"Invalid slot format: {slot}"
        
        print(f"SUCCESS: Available slots returned {len(slots)} slots")
        print(f"  First 5 slots: {slots[:5]}")
        
        # Verify 20:45 is NOT in slots (boundary check)
        assert "20:45" not in slots, "20:45 should not be available (boundary violation)"
        print("SUCCESS: 20:45 correctly not in available slots")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
