"""
Test new features for Salon Booking App:
1. Booking ID generation (4-char alphanumeric)
2. Payment status toggle (pending/paid)
3. Settings bank_account and payment_recipient fields
4. Worker deletion confirmation (backend validation)
"""

import pytest
import requests
import os
import random
import string

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"
TEST_PHONE = "+381641234567"

# Known IDs from context
WORKER_MILENA_ID = "69d0e529b3315e3608933158"
WORKER_SUZANA_ID = "69d0eb28b3315e360893315d"
WORKER_SLOBODAN_ID = "69d0f01754bd3450c6d78522"
SERVICE_SISANJE_ID = "69cf928a5bf25c5bf04b6c8f"
SERVICE_MANIKIR_ID = "69cf928a5bf25c5bf04b6c91"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestBookingIdGeneration:
    """Test that new reservations receive a unique booking_id"""
    
    def test_create_reservation_has_booking_id(self, auth_headers):
        """New reservation should have a 4-char alphanumeric booking_id"""
        # First get available slots for a future date
        test_date = "2026-02-20"
        
        # Get available slots
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE_ID, "worker_id": WORKER_SUZANA_ID}
            ],
            "date": test_date
        })
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        
        if not slots:
            pytest.skip("No available slots for test date")
        
        # Create reservation
        test_time = slots[0]
        unique_phone = f"+38164{random.randint(1000000, 9999999)}"
        
        create_response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE_ID, "worker_id": WORKER_SUZANA_ID}
            ],
            "date": test_date,
            "time": test_time,
            "client_name": "Test Booking ID",
            "client_phone": unique_phone
        })
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        data = create_response.json()
        
        # Verify booking_id exists and is 4 characters
        assert "booking_id" in data, "Response should contain booking_id"
        booking_id = data["booking_id"]
        assert len(booking_id) == 4, f"Booking ID should be 4 chars, got: {booking_id}"
        assert booking_id.isalnum(), f"Booking ID should be alphanumeric, got: {booking_id}"
        
        print(f"✓ Created reservation with booking_id: #{booking_id}")
        
        # Clean up - cancel the reservation
        res_id = data["id"]
        requests.put(f"{BASE_URL}/api/reservations/{res_id}/cancel", headers=auth_headers)
    
    def test_booking_id_in_reservations_list(self, auth_headers):
        """Booking ID should appear in admin reservations list"""
        response = requests.get(f"{BASE_URL}/api/reservations", headers=auth_headers)
        assert response.status_code == 200
        
        reservations = response.json()
        # Check that reservations have booking_id field (may be empty for old ones)
        for res in reservations:
            assert "booking_id" in res, "Reservation should have booking_id field"
        
        print(f"✓ All {len(reservations)} reservations have booking_id field")


class TestPaymentStatusToggle:
    """Test payment status toggle endpoint"""
    
    def test_toggle_payment_status_pending_to_paid(self, auth_headers):
        """Toggle payment status from pending to paid"""
        # First create a reservation
        test_date = "2026-02-21"
        
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE_ID, "worker_id": WORKER_SUZANA_ID}
            ],
            "date": test_date
        })
        assert slots_response.status_code == 200
        slots = slots_response.json().get("slots", [])
        
        if not slots:
            pytest.skip("No available slots for test date")
        
        unique_phone = f"+38164{random.randint(1000000, 9999999)}"
        create_response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE_ID, "worker_id": WORKER_SUZANA_ID}
            ],
            "date": test_date,
            "time": slots[0],
            "client_name": "Test Payment Status",
            "client_phone": unique_phone
        })
        
        assert create_response.status_code == 200
        res_data = create_response.json()
        res_id = res_data["id"]
        
        # Verify initial status is pending
        assert res_data.get("payment_status") == "pending", "Initial status should be pending"
        
        # Toggle to paid
        toggle_response = requests.put(
            f"{BASE_URL}/api/reservations/{res_id}/payment-status",
            headers=auth_headers
        )
        assert toggle_response.status_code == 200
        toggle_data = toggle_response.json()
        assert toggle_data.get("payment_status") == "paid", "Status should be paid after toggle"
        
        print(f"✓ Toggled payment status to 'paid'")
        
        # Toggle back to pending
        toggle_response2 = requests.put(
            f"{BASE_URL}/api/reservations/{res_id}/payment-status",
            headers=auth_headers
        )
        assert toggle_response2.status_code == 200
        toggle_data2 = toggle_response2.json()
        assert toggle_data2.get("payment_status") == "pending", "Status should be pending after second toggle"
        
        print(f"✓ Toggled payment status back to 'pending'")
        
        # Clean up
        requests.put(f"{BASE_URL}/api/reservations/{res_id}/cancel", headers=auth_headers)
    
    def test_payment_status_requires_auth(self):
        """Payment status toggle should require authentication"""
        response = requests.put(f"{BASE_URL}/api/reservations/fake-id/payment-status")
        assert response.status_code == 401, "Should require authentication"
        print("✓ Payment status endpoint requires authentication")
    
    def test_payment_status_not_found(self, auth_headers):
        """Toggle on non-existent reservation should return 404"""
        response = requests.put(
            f"{BASE_URL}/api/reservations/000000000000000000000000/payment-status",
            headers=auth_headers
        )
        assert response.status_code == 404, "Should return 404 for non-existent reservation"
        print("✓ Returns 404 for non-existent reservation")


class TestSettingsPaymentFields:
    """Test settings bank_account and payment_recipient fields"""
    
    def test_get_settings_has_payment_fields(self):
        """Settings should include bank_account and payment_recipient"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        
        data = response.json()
        assert "bank_account" in data, "Settings should have bank_account field"
        assert "payment_recipient" in data, "Settings should have payment_recipient field"
        
        print(f"✓ Settings has bank_account: {data.get('bank_account')}")
        print(f"✓ Settings has payment_recipient: {data.get('payment_recipient')}")
    
    def test_update_settings_payment_fields(self, auth_headers):
        """Admin can update bank_account and payment_recipient"""
        # Get current settings
        get_response = requests.get(f"{BASE_URL}/api/settings")
        original_settings = get_response.json()
        
        # Update with new values
        new_bank = "265-9999888877776-55"
        new_recipient = "Test Salon Updated"
        
        update_response = requests.put(f"{BASE_URL}/api/settings", json={
            "bank_account": new_bank,
            "payment_recipient": new_recipient
        }, headers=auth_headers)
        
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated.get("bank_account") == new_bank
        assert updated.get("payment_recipient") == new_recipient
        
        print(f"✓ Updated bank_account to: {new_bank}")
        print(f"✓ Updated payment_recipient to: {new_recipient}")
        
        # Restore original values
        requests.put(f"{BASE_URL}/api/settings", json={
            "bank_account": original_settings.get("bank_account", "265-1234567890123-12"),
            "payment_recipient": original_settings.get("payment_recipient", "Beauty Studio Bor")
        }, headers=auth_headers)


class TestWorkerDeletion:
    """Test worker deletion with future bookings validation"""
    
    def test_delete_worker_with_future_bookings_fails(self, auth_headers):
        """Cannot delete worker who has future bookings"""
        # Create a future reservation for Suzana
        test_date = "2026-02-25"
        
        slots_response = requests.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE_ID, "worker_id": WORKER_SUZANA_ID}
            ],
            "date": test_date
        })
        
        if slots_response.status_code != 200:
            pytest.skip("Could not get slots")
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots")
        
        unique_phone = f"+38164{random.randint(1000000, 9999999)}"
        create_response = requests.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_SISANJE_ID, "worker_id": WORKER_SUZANA_ID}
            ],
            "date": test_date,
            "time": slots[0],
            "client_name": "Test Worker Delete",
            "client_phone": unique_phone
        })
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test reservation")
        
        res_id = create_response.json()["id"]
        
        # Try to delete Suzana - should fail
        delete_response = requests.delete(
            f"{BASE_URL}/api/workers/{WORKER_SUZANA_ID}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 400, f"Should fail with 400, got {delete_response.status_code}"
        error_detail = delete_response.json().get("detail", "")
        assert "zakazane termine" in error_detail.lower() or "nije moguće" in error_detail.lower(), \
            f"Error should mention scheduled appointments: {error_detail}"
        
        print(f"✓ Cannot delete worker with future bookings: {error_detail}")
        
        # Clean up - cancel the reservation
        requests.put(f"{BASE_URL}/api/reservations/{res_id}/cancel", headers=auth_headers)
    
    def test_delete_worker_not_found(self, auth_headers):
        """Delete non-existent worker returns 404"""
        response = requests.delete(
            f"{BASE_URL}/api/workers/000000000000000000000000",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Returns 404 for non-existent worker")
    
    def test_delete_worker_requires_auth(self):
        """Worker deletion requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/workers/{WORKER_SUZANA_ID}")
        assert response.status_code == 401
        print("✓ Worker deletion requires authentication")


class TestReservationPaymentStatusInList:
    """Test that payment_status appears in reservation list"""
    
    def test_reservations_have_payment_status(self, auth_headers):
        """All reservations should have payment_status field"""
        response = requests.get(f"{BASE_URL}/api/reservations", headers=auth_headers)
        assert response.status_code == 200
        
        reservations = response.json()
        for res in reservations:
            assert "payment_status" in res, f"Reservation {res.get('id')} missing payment_status"
            assert res["payment_status"] in ["pending", "paid"], \
                f"Invalid payment_status: {res['payment_status']}"
        
        print(f"✓ All {len(reservations)} reservations have valid payment_status")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
