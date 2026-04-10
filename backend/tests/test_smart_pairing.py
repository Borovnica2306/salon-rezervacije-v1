"""
Test Smart Pairing Logic:
- 15-minute Social Buffer between consecutive services
- Anti-Conflict validation (same phone can't book overlapping times)
- All-or-Nothing chain validation
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test services from the problem statement
SERVICE_SISANJE = "69d3b77e0b47ad8f729e9ba2"  # 30min, worker Suzana
SERVICE_MANIKIR = "69d3b77e0b47ad8f729e9ba4"  # 45min, worker Milena
SERVICE_RELAX_MASAZA = "69d3b77e0b47ad8f729e9ba6"  # 60min, worker Slobodan

WORKER_SUZANA = "69d4d6f82990ad8a6366bf7d"
WORKER_MILENA = "69d4d6f82990ad8a6366bf7e"
WORKER_SLOBODAN = "69d4d6f82990ad8a6366bf7f"

# Test date - use future date to avoid timezone issues
TEST_DATE = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

# Admin credentials
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token for cleanup operations"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM to minutes"""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


class TestSocialBuffer:
    """Test 15-minute Social Buffer between consecutive services"""
    
    def test_single_service_no_buffer(self, api_client):
        """Single service should have NO gap (no buffer needed)"""
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": TEST_DATE
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "slots" in data, "Response should contain 'slots'"
        assert len(data["slots"]) > 0, "Should have available slots for single service"
        
        # Check slot_details - single service should have 0 gap
        if "slot_details" in data and data["slots"]:
            first_slot = data["slots"][0]
            slot_detail = data["slot_details"].get(first_slot, {})
            gap_minutes = slot_detail.get("gap_minutes", 0)
            assert gap_minutes == 0, f"Single service should have 0 gap, got {gap_minutes}"
            print(f"PASS: Single service has {gap_minutes} min gap (expected 0)")
    
    def test_two_services_exactly_15min_buffer(self, api_client):
        """Two services should have EXACTLY 15-minute gap between them"""
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},  # 30min
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}   # 45min
            ],
            "date": TEST_DATE
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "slots" in data, "Response should contain 'slots'"
        assert len(data["slots"]) > 0, "Should have available slots for 2 services"
        
        # Check slot_details for 15-min gap
        if "slot_details" in data and data["slots"]:
            first_slot = data["slots"][0]
            slot_detail = data["slot_details"].get(first_slot, {})
            
            # Total gap should be exactly 15 minutes (1 buffer between 2 services)
            gap_minutes = slot_detail.get("gap_minutes", 0)
            assert gap_minutes == 15, f"Two services should have exactly 15 min gap, got {gap_minutes}"
            
            # Verify time_blocks show the gap
            time_blocks = slot_detail.get("time_blocks", [])
            assert len(time_blocks) == 2, f"Should have 2 time blocks, got {len(time_blocks)}"
            
            # First block should have gap=0, second should have gap=15
            if len(time_blocks) >= 2:
                assert time_blocks[0].get("gap") == 0, f"First service gap should be 0, got {time_blocks[0].get('gap')}"
                assert time_blocks[1].get("gap") == 15, f"Second service gap should be 15, got {time_blocks[1].get('gap')}"
            
            print(f"PASS: Two services have {gap_minutes} min total gap (expected 15)")
            print(f"  Block 1 gap: {time_blocks[0].get('gap') if time_blocks else 'N/A'}")
            print(f"  Block 2 gap: {time_blocks[1].get('gap') if len(time_blocks) > 1 else 'N/A'}")
    
    def test_three_services_30min_total_buffer(self, api_client):
        """Three services should have 30-minute total gap (15 min between each pair)"""
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},      # 30min
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA},      # 45min
                {"service_id": SERVICE_RELAX_MASAZA, "worker_id": WORKER_SLOBODAN}  # 60min
            ],
            "date": TEST_DATE
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "slots" in data, "Response should contain 'slots'"
        # Note: May have fewer slots due to longer chain duration
        
        if "slot_details" in data and data["slots"]:
            first_slot = data["slots"][0]
            slot_detail = data["slot_details"].get(first_slot, {})
            
            # Total gap should be exactly 30 minutes (2 buffers between 3 services)
            gap_minutes = slot_detail.get("gap_minutes", 0)
            assert gap_minutes == 30, f"Three services should have exactly 30 min gap, got {gap_minutes}"
            
            # Verify time_blocks
            time_blocks = slot_detail.get("time_blocks", [])
            assert len(time_blocks) == 3, f"Should have 3 time blocks, got {len(time_blocks)}"
            
            # First block gap=0, second gap=15, third gap=15
            if len(time_blocks) >= 3:
                assert time_blocks[0].get("gap") == 0, f"First service gap should be 0"
                assert time_blocks[1].get("gap") == 15, f"Second service gap should be 15"
                assert time_blocks[2].get("gap") == 15, f"Third service gap should be 15"
            
            print(f"PASS: Three services have {gap_minutes} min total gap (expected 30)")
    
    def test_slot_timing_accuracy(self, api_client):
        """Verify actual start/end times include the 15-min buffer"""
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},  # 30min
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}   # 45min
            ],
            "date": TEST_DATE
        })
        
        assert response.status_code == 200
        data = response.json()
        
        if "slot_details" in data and data["slots"]:
            # Check a specific slot (e.g., 09:00)
            test_slot = "09:00"
            if test_slot in data["slot_details"]:
                slot_detail = data["slot_details"][test_slot]
                time_blocks = slot_detail.get("time_blocks", [])
                
                if len(time_blocks) >= 2:
                    # Service 1: 09:00 - 09:30 (30 min)
                    # Buffer: 15 min
                    # Service 2: 09:45 - 10:30 (45 min)
                    # Total: 90 min (30 + 15 + 45)
                    
                    block1_start = time_to_minutes(time_blocks[0]["start_time"])
                    block1_end = time_to_minutes(time_blocks[0]["end_time"])
                    block2_start = time_to_minutes(time_blocks[1]["start_time"])
                    block2_end = time_to_minutes(time_blocks[1]["end_time"])
                    
                    # Verify 15-min gap between end of service 1 and start of service 2
                    gap_between = block2_start - block1_end
                    assert gap_between == 15, f"Gap between services should be 15 min, got {gap_between}"
                    
                    # Verify total duration
                    total_duration = slot_detail.get("total_duration", 0)
                    expected_total = 30 + 15 + 45  # 90 min
                    assert total_duration == expected_total, f"Total duration should be {expected_total}, got {total_duration}"
                    
                    print(f"PASS: Slot timing verified - gap between services is {gap_between} min")
                    print(f"  Service 1: {time_blocks[0]['start_time']} - {time_blocks[0]['end_time']}")
                    print(f"  Service 2: {time_blocks[1]['start_time']} - {time_blocks[1]['end_time']}")


class TestAntiConflict:
    """Test Anti-Conflict validation - same phone can't book overlapping times"""
    
    def test_overlapping_same_phone_returns_409(self, api_client, admin_token):
        """Creating overlapping reservation with same phone should return 409"""
        test_phone = "0641111111"
        
        # First, get available slots
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": TEST_DATE
        })
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        assert len(slots) > 0, "Need available slots for test"
        
        test_time = slots[0]  # Use first available slot
        
        # Create first reservation
        res1 = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": TEST_DATE,
            "time": test_time,
            "client_name": "Test Client 1",
            "client_phone": test_phone
        })
        
        assert res1.status_code == 200, f"First reservation should succeed: {res1.text}"
        res1_id = res1.json().get("id")
        print(f"Created first reservation: {res1_id} at {test_time}")
        
        try:
            # Try to create overlapping reservation with SAME phone
            res2 = api_client.post(f"{BASE_URL}/api/reservations", json={
                "service_worker_pairs": [
                    {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}
                ],
                "date": TEST_DATE,
                "time": test_time,  # Same time = overlapping
                "client_name": "Test Client 1",
                "client_phone": test_phone  # Same phone
            })
            
            assert res2.status_code == 409, f"Overlapping reservation with same phone should return 409, got {res2.status_code}: {res2.text}"
            print(f"PASS: Overlapping reservation with same phone returned 409")
            print(f"  Error message: {res2.json().get('detail', 'N/A')}")
            
        finally:
            # Cleanup - cancel the first reservation
            if res1_id and admin_token:
                cancel_response = requests.put(
                    f"{BASE_URL}/api/reservations/{res1_id}/cancel",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                print(f"Cleanup: Cancelled reservation {res1_id}, status: {cancel_response.status_code}")
    
    def test_non_overlapping_same_phone_succeeds(self, api_client, admin_token):
        """Creating non-overlapping reservation with same phone should succeed"""
        test_phone = "0642222222"
        
        # Get available slots for first service (Milena - Manikir)
        slots_response1 = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}  # 45min
            ],
            "date": TEST_DATE
        })
        assert slots_response1.status_code == 200
        slots1 = slots_response1.json().get("slots", [])
        assert len(slots1) >= 2, "Need at least 2 slots for non-overlapping test"
        
        time1 = slots1[0]  # Early slot (e.g., 09:00)
        
        # Create first reservation with Milena
        res1 = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}
            ],
            "date": TEST_DATE,
            "time": time1,
            "client_name": "Test Client 2",
            "client_phone": test_phone
        })
        
        assert res1.status_code == 200, f"First reservation should succeed: {res1.text}"
        res1_id = res1.json().get("id")
        res1_end = res1.json().get("end_time")
        print(f"Created first reservation: {res1_id} at {time1} - {res1_end}")
        
        res2_id = None
        try:
            # Get available slots for second service (Suzana - Sisanje) AFTER first reservation
            slots_response2 = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
                "service_worker_pairs": [
                    {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}  # 30min, different worker
                ],
                "date": TEST_DATE
            })
            assert slots_response2.status_code == 200
            slots2 = slots_response2.json().get("slots", [])
            
            # Find a slot that doesn't overlap with first reservation
            # First reservation ends at res1_end, so pick a slot after that
            time2 = None
            for slot in slots2:
                if slot >= res1_end:  # Non-overlapping
                    time2 = slot
                    break
            
            assert time2 is not None, f"Should find non-overlapping slot after {res1_end}"
            
            # Create non-overlapping reservation with SAME phone but DIFFERENT worker
            res2 = api_client.post(f"{BASE_URL}/api/reservations", json={
                "service_worker_pairs": [
                    {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}  # Different worker
                ],
                "date": TEST_DATE,
                "time": time2,  # Non-overlapping time
                "client_name": "Test Client 2",
                "client_phone": test_phone  # Same phone
            })
            
            assert res2.status_code == 200, f"Non-overlapping reservation with same phone should succeed, got {res2.status_code}: {res2.text}"
            res2_id = res2.json().get("id")
            print(f"PASS: Non-overlapping reservation with same phone succeeded")
            print(f"  Reservation 1: {time1} - {res1_end}, Reservation 2: {time2}")
            
        finally:
            # Cleanup
            if admin_token:
                if res1_id:
                    requests.put(f"{BASE_URL}/api/reservations/{res1_id}/cancel",
                                headers={"Authorization": f"Bearer {admin_token}"})
                if res2_id:
                    requests.put(f"{BASE_URL}/api/reservations/{res2_id}/cancel",
                                headers={"Authorization": f"Bearer {admin_token}"})
                print(f"Cleanup: Cancelled test reservations")
    
    def test_overlapping_different_phone_succeeds(self, api_client, admin_token):
        """Creating overlapping reservation with DIFFERENT phone should succeed"""
        phone1 = "0643333333"
        phone2 = "0644444444"
        
        # Get available slots
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": TEST_DATE
        })
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        assert len(slots) > 0, "Need available slots for test"
        
        test_time = slots[0]
        
        # Create first reservation
        res1 = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA}
            ],
            "date": TEST_DATE,
            "time": test_time,
            "client_name": "Test Client 3",
            "client_phone": phone1
        })
        
        assert res1.status_code == 200, f"First reservation should succeed: {res1.text}"
        res1_id = res1.json().get("id")
        print(f"Created first reservation: {res1_id} at {test_time} with phone {phone1}")
        
        res2_id = None
        try:
            # Create overlapping reservation with DIFFERENT phone (different worker)
            res2 = api_client.post(f"{BASE_URL}/api/reservations", json={
                "service_worker_pairs": [
                    {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}  # Different worker
                ],
                "date": TEST_DATE,
                "time": test_time,  # Same time
                "client_name": "Test Client 4",
                "client_phone": phone2  # Different phone
            })
            
            assert res2.status_code == 200, f"Overlapping reservation with different phone should succeed, got {res2.status_code}: {res2.text}"
            res2_id = res2.json().get("id")
            print(f"PASS: Overlapping reservation with different phone succeeded")
            print(f"  Phone 1: {phone1}, Phone 2: {phone2}")
            
        finally:
            # Cleanup
            if admin_token:
                if res1_id:
                    requests.put(f"{BASE_URL}/api/reservations/{res1_id}/cancel",
                                headers={"Authorization": f"Bearer {admin_token}"})
                if res2_id:
                    requests.put(f"{BASE_URL}/api/reservations/{res2_id}/cancel",
                                headers={"Authorization": f"Bearer {admin_token}"})
                print(f"Cleanup: Cancelled test reservations")


class TestAllOrNothing:
    """Test All-or-Nothing chain validation"""
    
    def test_chain_rejected_if_worker_busy(self, api_client, admin_token):
        """2-service chain should be rejected if second worker is busy at buffer offset"""
        test_phone1 = "0645555555"
        test_phone2 = "0646666666"
        
        # Get available slots for a 2-service chain
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},  # 30min
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}   # 45min
            ],
            "date": TEST_DATE
        })
        assert slots_response.status_code == 200
        data = slots_response.json()
        slots = data.get("slots", [])
        assert len(slots) > 0, "Need available slots for test"
        
        test_time = slots[0]  # e.g., 09:00
        slot_detail = data.get("slot_details", {}).get(test_time, {})
        time_blocks = slot_detail.get("time_blocks", [])
        
        if len(time_blocks) >= 2:
            # The second service starts at buffer offset (e.g., 09:45 for 09:00 start)
            second_service_start = time_blocks[1]["start_time"]
            print(f"Chain at {test_time}: Service 2 starts at {second_service_start}")
            
            # First, book Milena (second worker) at the exact time the second service would start
            # This should make the chain unavailable at test_time
            res1 = api_client.post(f"{BASE_URL}/api/reservations", json={
                "service_worker_pairs": [
                    {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}
                ],
                "date": TEST_DATE,
                "time": second_service_start,  # Book Milena at the buffer offset time
                "client_name": "Blocker Client",
                "client_phone": test_phone1
            })
            
            assert res1.status_code == 200, f"Blocking reservation should succeed: {res1.text}"
            res1_id = res1.json().get("id")
            print(f"Created blocking reservation for Milena at {second_service_start}")
            
            try:
                # Now check if the original slot is still available for the chain
                slots_response2 = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
                    "service_worker_pairs": [
                        {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},
                        {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}
                    ],
                    "date": TEST_DATE
                })
                assert slots_response2.status_code == 200
                new_slots = slots_response2.json().get("slots", [])
                
                # The original test_time should NOT be in the available slots anymore
                assert test_time not in new_slots, f"Slot {test_time} should not be available when second worker is busy at buffer offset"
                print(f"PASS: Slot {test_time} correctly removed when Milena is busy at {second_service_start}")
                
            finally:
                # Cleanup
                if admin_token and res1_id:
                    requests.put(f"{BASE_URL}/api/reservations/{res1_id}/cancel",
                                headers={"Authorization": f"Bearer {admin_token}"})
                    print(f"Cleanup: Cancelled blocking reservation")


class TestReservationCreation:
    """Test reservation creation with proper time blocks"""
    
    def test_reservation_stores_time_blocks(self, api_client, admin_token):
        """Verify reservation stores worker_time_blocks with correct gaps"""
        test_phone = "0647777777"
        
        # Get available slots for 2-service chain
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}
            ],
            "date": TEST_DATE
        })
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        assert len(slots) > 0
        
        test_time = slots[0]
        
        # Create reservation
        res = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE, "worker_id": WORKER_SUZANA},
                {"service_id": SERVICE_MANIKIR, "worker_id": WORKER_MILENA}
            ],
            "date": TEST_DATE,
            "time": test_time,
            "client_name": "Test Client Time Blocks",
            "client_phone": test_phone
        })
        
        assert res.status_code == 200, f"Reservation should succeed: {res.text}"
        res_data = res.json()
        res_id = res_data.get("id")
        
        try:
            # Verify worker_time_blocks are stored
            time_blocks = res_data.get("worker_time_blocks", [])
            assert len(time_blocks) == 2, f"Should have 2 time blocks, got {len(time_blocks)}"
            
            # Verify gaps
            assert time_blocks[0].get("gap") == 0, "First block should have gap=0"
            assert time_blocks[1].get("gap") == 15, "Second block should have gap=15"
            
            # Verify total_duration includes buffer
            total_duration = res_data.get("total_duration", 0)
            expected = 30 + 15 + 45  # 90 min
            assert total_duration == expected, f"Total duration should be {expected}, got {total_duration}"
            
            print(f"PASS: Reservation stores correct time blocks with 15-min gap")
            print(f"  Time blocks: {time_blocks}")
            print(f"  Total duration: {total_duration} min")
            
        finally:
            # Cleanup
            if admin_token and res_id:
                requests.put(f"{BASE_URL}/api/reservations/{res_id}/cancel",
                            headers={"Authorization": f"Bearer {admin_token}"})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
