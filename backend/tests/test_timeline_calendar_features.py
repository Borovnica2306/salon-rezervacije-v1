"""
Test suite for Visual Timeline and Calendar features
Tests the new confirmation page features:
- Visual Timeline with service blocks and Social Buffer
- Google Calendar URL generation
- ICS download functionality
- worker_time_blocks in reservation response
"""

import pytest
import requests
import os
import random
import string
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test service/worker IDs from seed data
SISANJE_SERVICE_ID = "69d3b77e0b47ad8f729e9ba2"  # Šišanje (hair, 30min)
SUZANA_WORKER_ID = "69d4d6f82990ad8a6366bf7d"    # Suzana (hair worker)
RELAX_MASAZA_SERVICE_ID = "69d3b77e0b47ad8f729e9ba6"  # Relax masaža (massage, 60min)
SLOBODAN_WORKER_ID = "69d4d6f82990ad8a6366bf7f"  # Slobodan (massage worker)


def get_future_date(days_ahead=5):
    """Get a future date string in YYYY-MM-DD format"""
    future = datetime.now() + timedelta(days=days_ahead)
    # Skip weekends (assuming workers may have days off)
    while future.weekday() >= 5:  # Saturday=5, Sunday=6
        future += timedelta(days=1)
    return future.strftime("%Y-%m-%d")


def generate_test_phone():
    """Generate a unique test phone number"""
    return f"+38164{random.randint(1000000, 9999999)}"


class TestAvailableSlotsWithSocialBuffer:
    """Test POST /api/reservations/available-slots with Social Buffer"""
    
    def test_single_service_slots(self):
        """Single service should return slots without buffer"""
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_SERVICE_ID, "worker_id": SUZANA_WORKER_ID}
            ],
            "date": get_future_date(10)
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert len(data["slots"]) > 0
        print(f"Single service: {len(data['slots'])} slots available")
        
        # Check slot_details structure
        assert "slot_details" in data
        first_slot = data["slots"][0]
        detail = data["slot_details"].get(first_slot, {})
        
        # Single service should have 30 min duration, no gap
        assert detail.get("service_duration") == 30
        assert detail.get("gap_minutes") == 0
        print(f"Single service slot detail: {detail}")
    
    def test_multi_service_slots_with_15min_buffer(self):
        """Two services should have 15-minute Social Buffer between them"""
        response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_SERVICE_ID, "worker_id": SUZANA_WORKER_ID},
                {"service_id": RELAX_MASAZA_SERVICE_ID, "worker_id": SLOBODAN_WORKER_ID}
            ],
            "date": get_future_date(11)
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert len(data["slots"]) > 0
        print(f"Multi-service: {len(data['slots'])} slots available")
        
        # Check slot_details for buffer
        first_slot = data["slots"][0]
        detail = data["slot_details"].get(first_slot, {})
        
        # Total duration should be 30 + 60 = 90 min service + 15 min buffer = 105 min
        assert detail.get("total_duration") == 105, f"Expected 105 min, got {detail.get('total_duration')}"
        assert detail.get("service_duration") == 90, f"Expected 90 min service, got {detail.get('service_duration')}"
        assert detail.get("gap_minutes") == 15, f"Expected 15 min gap, got {detail.get('gap_minutes')}"
        
        # Check time_blocks structure
        time_blocks = detail.get("time_blocks", [])
        assert len(time_blocks) == 2, f"Expected 2 time blocks, got {len(time_blocks)}"
        
        # First block (Šišanje) should have gap=0
        assert time_blocks[0]["gap"] == 0
        assert time_blocks[0]["service_id"] == SISANJE_SERVICE_ID
        
        # Second block (Relax masaža) should have gap=15
        assert time_blocks[1]["gap"] == 15
        assert time_blocks[1]["service_id"] == RELAX_MASAZA_SERVICE_ID
        
        print(f"Multi-service slot detail: {detail}")
        print(f"Time blocks: {time_blocks}")


class TestReservationWithWorkerTimeBlocks:
    """Test POST /api/reservations returns worker_time_blocks"""
    
    def test_single_service_reservation(self):
        """Single service reservation should have worker_time_blocks"""
        # Get available slots first
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_SERVICE_ID, "worker_id": SUZANA_WORKER_ID}
            ],
            "date": get_future_date(12)
        })
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        assert len(slots) > 0
        
        # Create reservation
        response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_SERVICE_ID, "worker_id": SUZANA_WORKER_ID}
            ],
            "date": get_future_date(12),
            "time": slots[0],
            "client_name": f"Test Single {random.randint(1000, 9999)}",
            "client_phone": generate_test_phone()
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "booking_id" in data
        assert "worker_time_blocks" in data
        assert "service_worker_pairs" in data
        assert "total_duration" in data
        assert "end_time" in data
        
        # Single service should have 1 time block
        assert len(data["worker_time_blocks"]) == 1
        block = data["worker_time_blocks"][0]
        assert block["service_id"] == SISANJE_SERVICE_ID
        assert block["worker_id"] == SUZANA_WORKER_ID
        assert block["gap"] == 0
        
        print(f"Single service reservation: {data['booking_id']}")
        print(f"Worker time blocks: {data['worker_time_blocks']}")
    
    def test_multi_service_reservation_with_buffer(self):
        """Multi-service reservation should have worker_time_blocks with gap info"""
        # Get available slots first
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_SERVICE_ID, "worker_id": SUZANA_WORKER_ID},
                {"service_id": RELAX_MASAZA_SERVICE_ID, "worker_id": SLOBODAN_WORKER_ID}
            ],
            "date": get_future_date(13)
        })
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        assert len(slots) > 0
        
        # Create reservation
        response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_SERVICE_ID, "worker_id": SUZANA_WORKER_ID},
                {"service_id": RELAX_MASAZA_SERVICE_ID, "worker_id": SLOBODAN_WORKER_ID}
            ],
            "date": get_future_date(13),
            "time": slots[0],
            "client_name": f"Test Multi {random.randint(1000, 9999)}",
            "client_phone": generate_test_phone()
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "booking_id" in data
        assert "worker_time_blocks" in data
        assert len(data["worker_time_blocks"]) == 2
        
        # First block should have gap=0
        assert data["worker_time_blocks"][0]["gap"] == 0
        assert data["worker_time_blocks"][0]["service_id"] == SISANJE_SERVICE_ID
        
        # Second block should have gap=15 (Social Buffer)
        assert data["worker_time_blocks"][1]["gap"] == 15
        assert data["worker_time_blocks"][1]["service_id"] == RELAX_MASAZA_SERVICE_ID
        
        # Total duration should be 105 min (30 + 15 buffer + 60)
        assert data["total_duration"] == 105
        
        # Verify service_worker_pairs
        assert len(data["service_worker_pairs"]) == 2
        assert data["service_worker_pairs"][0]["service_name"] == "Šišanje"
        assert data["service_worker_pairs"][0]["worker_name"] == "Suzana"
        assert data["service_worker_pairs"][1]["service_name"] == "Relax masaža"
        assert data["service_worker_pairs"][1]["worker_name"] == "Slobodan"
        
        print(f"Multi-service reservation: {data['booking_id']}")
        print(f"Worker time blocks: {data['worker_time_blocks']}")
        print(f"Total duration: {data['total_duration']} min")


class TestReservationResponseForCalendar:
    """Test reservation response has all fields needed for calendar features"""
    
    def test_reservation_has_calendar_fields(self):
        """Reservation response should have all fields for Google Calendar and ICS"""
        # Get available slots
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_SERVICE_ID, "worker_id": SUZANA_WORKER_ID}
            ],
            "date": get_future_date(14)
        })
        slots = slots_response.json().get("slots", [])
        
        # Create reservation
        response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SISANJE_SERVICE_ID, "worker_id": SUZANA_WORKER_ID}
            ],
            "date": get_future_date(14),
            "time": slots[0],
            "client_name": f"Calendar Test {random.randint(1000, 9999)}",
            "client_phone": generate_test_phone()
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Fields needed for Google Calendar URL
        assert "date" in data  # YYYY-MM-DD format
        assert "time" in data  # HH:MM format
        assert "end_time" in data  # HH:MM format
        assert "booking_id" in data
        assert "service_names" in data
        
        # Verify date format
        assert len(data["date"]) == 10  # YYYY-MM-DD
        assert "-" in data["date"]
        
        # Verify time format
        assert ":" in data["time"]
        assert ":" in data["end_time"]
        
        # Verify service_names is a list
        assert isinstance(data["service_names"], list)
        assert len(data["service_names"]) > 0
        
        print(f"Calendar fields verified for booking {data['booking_id']}")
        print(f"Date: {data['date']}, Time: {data['time']} - {data['end_time']}")
        print(f"Services: {data['service_names']}")


class TestSettingsForPaymentInfo:
    """Test settings endpoint returns payment info for confirmation page"""
    
    def test_settings_has_payment_fields(self):
        """Settings should have bank_account and payment_recipient"""
        response = requests.get(f"{BASE_URL}/api/settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        assert "salon_name" in data
        assert "bank_account" in data
        assert "payment_recipient" in data
        
        print(f"Settings: salon_name={data['salon_name']}")
        print(f"Bank account: {data.get('bank_account', 'N/A')}")
        print(f"Payment recipient: {data.get('payment_recipient', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
