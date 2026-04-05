"""
Split-Booking and Salon Booking API Tests
Tests for:
- Split-booking: POST /api/reservations/available-slots with multiple service_worker_pairs
- Split-booking: Conflict prevention - worker time blocks correctly blocked
- Split-booking: Gap only applies between services, not before first service
- POST /api/reservations creates booking with worker_time_blocks stored correctly
- Phone blacklist blocks bookings
- Max 3 reservations per phone per day
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data from the review request
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"
TEST_PHONE = "+381641234567"

# Worker IDs
MILENA_ID = "69d0e529b3315e3608933158"  # nails
SUZANA_ID = "69d0eb28b3315e360893315d"  # hair
SLOBODAN_ID = "69d0f01754bd3450c6d78522"  # massage

# Service IDs
SISANJE_ID = "69cf928a5bf25c5bf04b6c8f"  # 30min, hair
MANIKIR_ID = "69cf928a5bf25c5bf04b6c91"  # 45min, nails

TODAY = "2026-04-05"
TOMORROW = "2026-04-06"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self, api_client):
        """Test API root endpoint"""
        response = api_client.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Salon Booking API"
        print("✓ API root endpoint working")
    
    def test_services_endpoint(self, api_client):
        """Test services endpoint returns data"""
        response = api_client.get(f"{BASE_URL}/api/services")
        assert response.status_code == 200
        services = response.json()
        assert isinstance(services, list)
        assert len(services) > 0
        # Verify Šišanje and Manikir exist
        service_names = [s["name"] for s in services]
        assert "Šišanje" in service_names
        assert "Manikir" in service_names
        print(f"✓ Services endpoint returns {len(services)} services")
    
    def test_workers_endpoint(self, api_client):
        """Test workers endpoint returns data"""
        response = api_client.get(f"{BASE_URL}/api/workers")
        assert response.status_code == 200
        workers = response.json()
        assert isinstance(workers, list)
        assert len(workers) >= 3
        # Verify expected workers exist
        worker_names = [w["name"] for w in workers]
        assert "Milena" in worker_names
        assert "Suzana" in worker_names
        assert "Slobodan" in worker_names
        print(f"✓ Workers endpoint returns {len(workers)} workers")


class TestSplitBookingAvailableSlots:
    """Tests for split-booking available-slots endpoint"""
    
    def test_available_slots_single_service(self, api_client):
        """Test available slots for single service/worker pair"""
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TOMORROW
        })
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert "slot_details" in data
        assert len(data["slots"]) > 0
        print(f"✓ Single service returns {len(data['slots'])} available slots")
    
    def test_available_slots_multiple_services(self, api_client):
        """Test available slots for multiple service/worker pairs (split-booking)"""
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID},
                {"service_id": MANIKIR_ID, "worker_id": MILENA_ID}
            ],
            "date": TOMORROW
        })
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert "slot_details" in data
        assert len(data["slots"]) > 0
        
        # Verify slot_details structure
        first_slot = data["slots"][0]
        slot_detail = data["slot_details"][first_slot]
        assert "end_time" in slot_detail
        assert "total_duration" in slot_detail
        assert "time_blocks" in slot_detail
        assert len(slot_detail["time_blocks"]) == 2  # Two services
        
        # Verify time_blocks have correct structure
        for block in slot_detail["time_blocks"]:
            assert "worker_id" in block
            assert "service_id" in block
            assert "start_time" in block
            assert "end_time" in block
            assert "gap" in block
        
        print(f"✓ Split-booking returns {len(data['slots'])} slots with correct time_blocks structure")
    
    def test_gap_only_between_services(self, api_client):
        """Test that gap only applies between services, not before first service"""
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID},
                {"service_id": MANIKIR_ID, "worker_id": MILENA_ID}
            ],
            "date": TOMORROW
        })
        assert response.status_code == 200
        data = response.json()
        
        # Check first slot - first service should have gap=0
        first_slot = data["slots"][0]
        slot_detail = data["slot_details"][first_slot]
        
        # First service should always have gap=0
        first_block = slot_detail["time_blocks"][0]
        assert first_block["gap"] == 0, "First service should have no gap before it"
        
        # First service start_time should match slot time
        assert first_block["start_time"] == first_slot, "First service should start at slot time"
        
        print("✓ Gap only applies between services, not before first service")
    
    def test_sequential_time_blocks(self, api_client):
        """Test that time blocks are sequential"""
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID},
                {"service_id": MANIKIR_ID, "worker_id": MILENA_ID}
            ],
            "date": TOMORROW
        })
        assert response.status_code == 200
        data = response.json()
        
        first_slot = data["slots"][0]
        slot_detail = data["slot_details"][first_slot]
        blocks = slot_detail["time_blocks"]
        
        # Verify sequential: second service starts at or after first service ends
        first_end = blocks[0]["end_time"]
        second_start = blocks[1]["start_time"]
        
        # Convert to minutes for comparison
        def time_to_min(t):
            h, m = map(int, t.split(":"))
            return h * 60 + m
        
        first_end_min = time_to_min(first_end)
        second_start_min = time_to_min(second_start)
        
        assert second_start_min >= first_end_min, "Second service should start at or after first ends"
        assert second_start_min <= first_end_min + 15, "Gap should be max 15 minutes"
        
        print("✓ Time blocks are sequential with max 15-min gap")


class TestConflictPrevention:
    """Tests for conflict prevention after booking"""
    
    def test_existing_reservation_blocks_slots(self, api_client):
        """Test that existing reservation blocks the correct time slots"""
        # There's an existing reservation at 15:00-16:15 for Suzana (Šišanje) and Milena (Manikir)
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID},
                {"service_id": MANIKIR_ID, "worker_id": MILENA_ID}
            ],
            "date": TODAY
        })
        assert response.status_code == 200
        data = response.json()
        
        # 15:00 should NOT be available (existing reservation)
        assert "15:00" not in data["slots"], "15:00 should be blocked by existing reservation"
        
        # 15:15 should also be blocked (overlaps with existing)
        assert "15:15" not in data["slots"], "15:15 should be blocked by existing reservation"
        
        print("✓ Existing reservation correctly blocks time slots")
    
    def test_individual_worker_blocking(self, api_client):
        """Test that individual worker time blocks are correctly blocked"""
        # Existing reservation: Suzana 15:00-15:30, Milena 15:30-16:15
        
        # Try to book just Suzana for Šišanje - 15:00 should be blocked
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TODAY
        })
        assert response.status_code == 200
        data = response.json()
        
        # Suzana is blocked 15:00-15:30
        assert "15:00" not in data["slots"], "Suzana should be blocked at 15:00"
        assert "15:15" not in data["slots"], "Suzana should be blocked at 15:15"
        
        # But 15:30 should be available for Suzana (her block ends at 15:30)
        assert "15:30" in data["slots"], "Suzana should be available at 15:30"
        
        print("✓ Individual worker time blocks correctly blocked")


class TestReservationCreation:
    """Tests for reservation creation with worker_time_blocks"""
    
    def test_create_split_booking_reservation(self, api_client):
        """Test creating a split-booking reservation stores worker_time_blocks"""
        # Use a unique phone to avoid conflicts
        import random
        test_phone = f"+38169{random.randint(1000000, 9999999)}"
        
        # First get available slots to find a valid time
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID},
                {"service_id": MANIKIR_ID, "worker_id": MILENA_ID}
            ],
            "date": TOMORROW
        })
        assert slots_response.status_code == 200
        available_slots = slots_response.json().get("slots", [])
        assert len(available_slots) > 0, "No available slots for tomorrow"
        
        # Use the first available slot
        selected_time = available_slots[0]
        
        response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID},
                {"service_id": MANIKIR_ID, "worker_id": MILENA_ID}
            ],
            "date": TOMORROW,
            "time": selected_time,
            "client_name": "Test Split Booking",
            "client_phone": test_phone
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "service_worker_pairs" in data
        assert "worker_time_blocks" in data
        assert len(data["service_worker_pairs"]) == 2
        assert len(data["worker_time_blocks"]) == 2
        
        # Verify worker_time_blocks structure
        for block in data["worker_time_blocks"]:
            assert "worker_id" in block
            assert "service_id" in block
            assert "start_time" in block
            assert "end_time" in block
        
        # Verify service_worker_pairs have names
        for pair in data["service_worker_pairs"]:
            assert "service_name" in pair
            assert "worker_name" in pair
        
        print(f"✓ Split-booking reservation created with ID: {data['id']}")
        print(f"  - worker_time_blocks: {data['worker_time_blocks']}")
        
        return data["id"]


class TestBlacklist:
    """Tests for phone blacklist functionality"""
    
    def test_blacklist_blocks_booking(self, api_client, authenticated_client):
        """Test that blacklisted phone cannot make bookings"""
        blacklist_phone = "381600000001"
        
        # Add phone to blacklist
        response = authenticated_client.post(
            f"{BASE_URL}/api/blacklist?phone={blacklist_phone}"
        )
        assert response.status_code == 200
        print(f"✓ Phone {blacklist_phone} added to blacklist")
        
        # Try to make a booking with blacklisted phone
        response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TOMORROW,
            "time": "11:00",
            "client_name": "Blacklisted User",
            "client_phone": f"+{blacklist_phone}"
        })
        
        assert response.status_code == 403
        assert "blokiran" in response.json()["detail"].lower()
        print("✓ Blacklisted phone correctly blocked from booking")
        
        # Clean up - remove from blacklist
        authenticated_client.delete(f"{BASE_URL}/api/blacklist/{blacklist_phone}")
    
    def test_get_blacklist(self, authenticated_client):
        """Test getting blacklist"""
        response = authenticated_client.get(f"{BASE_URL}/api/blacklist")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Blacklist endpoint returns {len(data)} entries")


class TestDailyLimit:
    """Tests for max 3 reservations per phone per day"""
    
    def test_max_3_reservations_per_day(self, api_client):
        """Test that max 3 reservations per phone per day is enforced"""
        test_phone = "+381688888888"
        
        # Create 3 reservations
        times = ["09:00", "11:00", "17:00"]
        created_ids = []
        
        for i, time in enumerate(times):
            response = api_client.post(f"{BASE_URL}/api/reservations", json={
                "service_worker_pairs": [
                    {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
                ],
                "date": TOMORROW,
                "time": time,
                "client_name": f"Test Limit User {i+1}",
                "client_phone": test_phone
            })
            
            if response.status_code == 200:
                created_ids.append(response.json()["id"])
                print(f"✓ Reservation {i+1} created at {time}")
            else:
                print(f"  Reservation {i+1} failed: {response.json()}")
        
        # Try to create 4th reservation - should fail
        response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TOMORROW,
            "time": "18:00",
            "client_name": "Test Limit User 4",
            "client_phone": test_phone
        })
        
        assert response.status_code == 400
        assert "3" in response.json()["detail"] or "maksimalno" in response.json()["detail"].lower()
        print("✓ 4th reservation correctly rejected (max 3 per day)")


class TestMyReservations:
    """Tests for client 'Moje rezervacije' functionality"""
    
    def test_get_my_reservations(self, api_client):
        """Test getting reservations by phone number"""
        # Use the existing test phone that has a reservation
        response = api_client.post(f"{BASE_URL}/api/my-reservations", json={
            "phone": TEST_PHONE
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            res = data[0]
            assert "id" in res
            assert "date" in res
            assert "time" in res
            assert "services" in res
            assert "can_cancel" in res
            print(f"✓ Found {len(data)} reservations for phone {TEST_PHONE}")
        else:
            print(f"✓ No reservations found for phone {TEST_PHONE} (expected if none exist)")
    
    def test_cancel_own_reservation(self, api_client):
        """Test client canceling their own reservation"""
        # First create a reservation for tomorrow (can be cancelled)
        test_phone = "+381677777777"
        
        response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_ID, "worker_id": SUZANA_ID}
            ],
            "date": TOMORROW,
            "time": "12:00",
            "client_name": "Cancel Test User",
            "client_phone": test_phone
        })
        
        if response.status_code != 200:
            pytest.skip(f"Could not create test reservation: {response.json()}")
        
        reservation_id = response.json()["id"]
        print(f"✓ Created test reservation {reservation_id}")
        
        # Cancel the reservation
        response = api_client.put(
            f"{BASE_URL}/api/my-reservations/{reservation_id}/cancel",
            json={"phone": test_phone}
        )
        
        assert response.status_code == 200
        print("✓ Client successfully cancelled their reservation")


class TestAdminReservations:
    """Tests for admin reservations endpoint"""
    
    def test_get_reservations_with_service_worker_pairs(self, authenticated_client):
        """Test that admin reservations endpoint returns service_worker_pairs"""
        response = authenticated_client.get(f"{BASE_URL}/api/reservations?date={TODAY}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            res = data[0]
            assert "service_worker_pairs" in res
            assert "worker_time_blocks" in res
            
            # Verify service_worker_pairs structure
            if len(res["service_worker_pairs"]) > 0:
                pair = res["service_worker_pairs"][0]
                assert "service_name" in pair
                assert "worker_name" in pair
                print(f"✓ Reservation has service_worker_pairs: {res['service_worker_pairs']}")
        
        print(f"✓ Admin reservations endpoint returns {len(data)} reservations")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
