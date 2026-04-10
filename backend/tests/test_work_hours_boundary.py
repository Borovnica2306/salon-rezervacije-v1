"""
Test Work Hours Boundary Check Feature
======================================
Tests for strict per-worker work hours enforcement:
- Single service boundary validation
- Multi-service chain boundary validation
- Admin force-override capability
- Client booking restrictions
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data from review request
SUZANA_ID = "69d4d6f82990ad8a6366bf7d"  # Works 09:00-21:00
MILENA_ID = "69d4d6f82990ad8a6366bf7e"  # Works 09:00-21:00
SISANJE_ID = "69d3b77e0b47ad8f729e9ba2"  # 30min
MANIKIR_ID = "69d3b77e0b47ad8f729e9ba4"  # 45min

# Use future date to avoid timezone issues
TEST_DATE = "2026-04-25"

# Admin credentials
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"


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


@pytest.fixture(scope="module")
def admin_session(admin_token):
    """Session with admin auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    })
    return session


class TestSingleServiceBoundary:
    """Test single service boundary validation (30min Šišanje)"""
    
    def test_slot_2030_is_available_for_suzana(self):
        """
        20:30 + 30min = 21:00 (exactly at boundary)
        Should be in available slots
        """
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        slots = data.get("slots", [])
        
        # 20:30 should be available (finishes exactly at 21:00)
        assert "20:30" in slots, f"20:30 should be available. Available slots: {slots[-10:]}"
        print(f"✓ 20:30 is available (finishes at 21:00 - exactly at boundary)")
    
    def test_slot_2045_is_not_available_for_suzana(self):
        """
        20:45 + 30min = 21:15 (past boundary)
        Should NOT be in available slots
        """
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        slots = data.get("slots", [])
        
        # 20:45 should NOT be available (would finish at 21:15)
        assert "20:45" not in slots, f"20:45 should NOT be available (would finish at 21:15). Last slots: {slots[-5:]}"
        print(f"✓ 20:45 is NOT available (would finish at 21:15 - past boundary)")
    
    def test_last_available_slot_is_2030(self):
        """
        Last available slot for 30min service should be 20:30
        """
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        slots = data.get("slots", [])
        
        if slots:
            last_slot = slots[-1]
            assert last_slot == "20:30", f"Last slot should be 20:30, got {last_slot}"
            print(f"✓ Last available slot is 20:30")


class TestTwoServiceChainBoundary:
    """
    Test 2-service chain boundary validation
    Šišanje (30min) + Manikir (45min) = 75min + 15min buffer = 90min total
    Last slot should end exactly at 21:00
    """
    
    def test_chain_last_slot_ends_at_2100(self):
        """
        2-service chain: 30min + 15min buffer + 45min = 90min
        Last valid start: 21:00 - 90min = 19:30
        19:30 + 90min = 21:00 (exactly at boundary)
        """
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID},
                {"service_id": MANIKIR_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        slots = data.get("slots", [])
        slot_details = data.get("slot_details", {})
        
        # 19:30 should be available
        assert "19:30" in slots, f"19:30 should be available for 2-service chain. Last slots: {slots[-5:]}"
        
        # Verify end time is exactly 21:00
        if "19:30" in slot_details:
            end_time = slot_details["19:30"].get("end_time")
            assert end_time == "21:00", f"19:30 slot should end at 21:00, got {end_time}"
            print(f"✓ 19:30 slot ends at 21:00 (exactly at boundary)")
    
    def test_chain_1945_is_not_available(self):
        """
        19:45 + 90min = 21:15 (past boundary)
        Should NOT be available
        """
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID},
                {"service_id": MANIKIR_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        slots = data.get("slots", [])
        
        # 19:45 should NOT be available (would finish at 21:15)
        assert "19:45" not in slots, f"19:45 should NOT be available for 2-service chain. Last slots: {slots[-5:]}"
        print(f"✓ 19:45 is NOT available for 2-service chain (would finish at 21:15)")


class TestPerWorkerHours:
    """Test that available slots respect individual worker hours, not global window"""
    
    def test_slots_respect_individual_worker_hours(self):
        """
        Each worker's own work hours should be enforced
        """
        # Get slots for Suzana
        response_suzana = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE
        })
        assert response_suzana.status_code == 200
        slots_suzana = response_suzana.json().get("slots", [])
        
        # Get slots for Milena
        response_milena = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": MILENA_ID}
            ],
            "date": TEST_DATE
        })
        assert response_milena.status_code == 200
        slots_milena = response_milena.json().get("slots", [])
        
        # Both workers have same hours (09:00-21:00), so slots should be similar
        # But the key is that each worker's hours are checked individually
        assert len(slots_suzana) > 0, "Suzana should have available slots"
        assert len(slots_milena) > 0, "Milena should have available slots"
        
        # Both should have 20:30 as last slot for 30min service
        assert "20:30" in slots_suzana, "Suzana should have 20:30 slot"
        assert "20:30" in slots_milena, "Milena should have 20:30 slot"
        
        # Neither should have 20:45
        assert "20:45" not in slots_suzana, "Suzana should NOT have 20:45 slot"
        assert "20:45" not in slots_milena, "Milena should NOT have 20:45 slot"
        
        print(f"✓ Both workers respect their individual work hours (09:00-21:00)")


class TestAdminBoundaryViolation:
    """Test admin booking with boundary violations"""
    
    def test_admin_booking_2045_returns_409_with_boundary_warning(self, admin_session):
        """
        Admin POST at 20:45 should return 409 with boundary violation message
        mentioning worker name
        """
        response = admin_session.post(f"{BASE_URL}/api/admin/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE,
            "time": "20:45",
            "client_name": "Test Boundary",
            "client_phone": "0641234567",
            "force": False
        })
        
        assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.text}"
        
        detail = response.json().get("detail", "")
        # Should mention worker name and boundary violation
        assert "Suzana" in detail, f"Warning should mention worker name 'Suzana'. Got: {detail}"
        assert "21:00" in detail or "21:15" in detail, f"Warning should mention work end time. Got: {detail}"
        
        print(f"✓ Admin booking at 20:45 returns 409 with boundary warning: {detail}")
    
    def test_admin_booking_2045_with_force_succeeds(self, admin_session):
        """
        Admin POST at 20:45 with force=true should succeed despite boundary violation
        """
        response = admin_session.post(f"{BASE_URL}/api/admin/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE,
            "time": "20:45",
            "client_name": "Test Force Override",
            "client_phone": "0641234568",
            "force": True
        })
        
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("time") == "20:45", f"Booking time should be 20:45"
        assert data.get("end_time") == "21:15", f"End time should be 21:15"
        
        # Clean up - cancel the test reservation
        reservation_id = data.get("id")
        if reservation_id:
            cancel_response = admin_session.put(f"{BASE_URL}/api/reservations/{reservation_id}/cancel")
            print(f"Cleanup: Cancelled test reservation {reservation_id}")
        
        print(f"✓ Admin force booking at 20:45 succeeded (end time: 21:15)")
    
    def test_admin_booking_2030_succeeds_without_warnings(self, admin_session):
        """
        Admin POST at 20:30 (exact boundary) should succeed without warnings
        """
        response = admin_session.post(f"{BASE_URL}/api/admin/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE,
            "time": "20:30",
            "client_name": "Test Exact Boundary",
            "client_phone": "0641234569",
            "force": False
        })
        
        # Should succeed (200/201) without needing force
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("time") == "20:30", f"Booking time should be 20:30"
        assert data.get("end_time") == "21:00", f"End time should be 21:00"
        
        # Clean up
        reservation_id = data.get("id")
        if reservation_id:
            cancel_response = admin_session.put(f"{BASE_URL}/api/reservations/{reservation_id}/cancel")
            print(f"Cleanup: Cancelled test reservation {reservation_id}")
        
        print(f"✓ Admin booking at 20:30 succeeded without warnings (end time: 21:00)")


class TestClientBoundaryRestriction:
    """Test that clients cannot book past boundary"""
    
    def test_client_cannot_book_2045(self):
        """
        Client POST at 20:45 should fail with 'Izabrani termin više nije dostupan'
        """
        response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE,
            "time": "20:45",
            "client_name": "Test Client Boundary",
            "client_phone": "0641234570"
        })
        
        # Should fail because 20:45 is not in available slots
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        
        detail = response.json().get("detail", "")
        assert "nije dostupan" in detail.lower() or "not available" in detail.lower(), \
            f"Error should mention slot not available. Got: {detail}"
        
        print(f"✓ Client booking at 20:45 rejected: {detail}")
    
    def test_client_can_book_2030(self):
        """
        Client POST at 20:30 should succeed (exactly at boundary)
        """
        response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TEST_DATE,
            "time": "20:30",
            "client_name": "Test Client Valid",
            "client_phone": "0641234571"
        })
        
        # Should succeed
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("time") == "20:30"
        assert data.get("end_time") == "21:00"
        
        # Clean up - need admin to cancel
        print(f"✓ Client booking at 20:30 succeeded. Reservation ID: {data.get('id')}")
        print(f"  Note: Test reservation created - should be cleaned up via admin cancel")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
