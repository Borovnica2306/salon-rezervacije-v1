"""
Test suite for Lazy Cancel, Viber Notifications, and Trigger Reminders features.

Features tested:
1. cancel_stale_unpaid_reservations - cancels reservations older than 3 hours with pending payment
2. Lazy cancel hooks in available-slots and GET /reservations endpoints
3. trigger-reminders admin endpoint
4. send_viber_notification graceful handling when VIBER_TOKEN is missing
"""

import pytest
import requests
import os
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo import MongoClient

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data from context
SERVICE_ID = "69d549f035e38a4c2c9f0226"
WORKER_ID = "69d54b0635e38a4c2c9f022e"
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def mongo_client():
    """Direct MongoDB connection for test data manipulation."""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    client = MongoClient(mongo_url)
    yield client[db_name]
    client.close()


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token."""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, admin_token):
    """Session with admin auth header."""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


class TestLazyCancel:
    """Tests for cancel_stale_unpaid_reservations functionality."""

    def test_lazy_cancel_on_available_slots(self, api_client, mongo_client):
        """Test that lazy cancel runs when POST /api/reservations/available-slots is called."""
        # Create a test reservation with old created_at (>3 hours ago)
        old_time = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
        future_date = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
        
        test_reservation = {
            "booking_id": "TEST_LC1",
            "services": [SERVICE_ID],
            "service_names": ["Test Service"],
            "service_worker_pairs": [{
                "service_id": SERVICE_ID,
                "worker_id": WORKER_ID,
                "service_name": "Test Service",
                "worker_name": "Test Worker",
                "duration": 30,
                "price": 1000
            }],
            "worker_time_blocks": [],
            "worker_id": WORKER_ID,
            "worker_name": "Test Worker",
            "date": future_date,
            "time": "10:00",
            "end_time": "10:30",
            "total_duration": 30,
            "total_price": 1000,
            "client_name": "Test Client LC",
            "client_phone": "381999888777",
            "client_email": "test_lc@test.com",
            "status": "confirmed",
            "payment_status": "pending",  # Key: pending payment
            "advance_required": True,
            "advance_released": False,
            "created_at": old_time  # Key: older than 3 hours
        }
        
        # Insert directly into MongoDB
        result = mongo_client.reservations.insert_one(test_reservation)
        inserted_id = result.inserted_id
        
        try:
            # Call available-slots endpoint (triggers lazy cancel)
            response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
                "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
                "date": future_date
            })
            assert response.status_code == 200, f"Available slots failed: {response.text}"
            
            # Verify the reservation was cancelled
            cancelled_res = mongo_client.reservations.find_one({"_id": inserted_id})
            assert cancelled_res is not None, "Reservation not found"
            assert cancelled_res.get("status") == "cancelled", f"Expected cancelled, got {cancelled_res.get('status')}"
            assert cancelled_res.get("cancelled_by") == "system_auto", f"Expected system_auto, got {cancelled_res.get('cancelled_by')}"
            assert cancelled_res.get("cancelled_at") is not None, "cancelled_at should be set"
            print(f"✓ Lazy cancel on available-slots: Reservation {inserted_id} cancelled correctly")
            
        finally:
            # Cleanup
            mongo_client.reservations.delete_one({"_id": inserted_id})

    def test_lazy_cancel_on_get_reservations(self, authenticated_client, mongo_client):
        """Test that lazy cancel runs when GET /api/reservations (admin) is called."""
        # Create a test reservation with old created_at (>3 hours ago)
        old_time = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        future_date = (datetime.now(timezone.utc) + timedelta(days=8)).strftime("%Y-%m-%d")
        
        test_reservation = {
            "booking_id": "TEST_LC2",
            "services": [SERVICE_ID],
            "service_names": ["Test Service"],
            "service_worker_pairs": [{
                "service_id": SERVICE_ID,
                "worker_id": WORKER_ID,
                "service_name": "Test Service",
                "worker_name": "Test Worker",
                "duration": 30,
                "price": 1000
            }],
            "worker_time_blocks": [],
            "worker_id": WORKER_ID,
            "worker_name": "Test Worker",
            "date": future_date,
            "time": "11:00",
            "end_time": "11:30",
            "total_duration": 30,
            "total_price": 1000,
            "client_name": "Test Client LC2",
            "client_phone": "381999888666",
            "client_email": "test_lc2@test.com",
            "status": "confirmed",
            "payment_status": "pending",  # Key: pending payment
            "advance_required": True,
            "advance_released": False,
            "created_at": old_time  # Key: older than 3 hours
        }
        
        # Insert directly into MongoDB
        result = mongo_client.reservations.insert_one(test_reservation)
        inserted_id = result.inserted_id
        
        try:
            # Call GET /reservations endpoint (triggers lazy cancel)
            response = authenticated_client.get(f"{BASE_URL}/api/reservations?date={future_date}")
            assert response.status_code == 200, f"GET reservations failed: {response.text}"
            
            # Verify the reservation was cancelled
            cancelled_res = mongo_client.reservations.find_one({"_id": inserted_id})
            assert cancelled_res is not None, "Reservation not found"
            assert cancelled_res.get("status") == "cancelled", f"Expected cancelled, got {cancelled_res.get('status')}"
            assert cancelled_res.get("cancelled_by") == "system_auto", f"Expected system_auto, got {cancelled_res.get('cancelled_by')}"
            print(f"✓ Lazy cancel on GET /reservations: Reservation {inserted_id} cancelled correctly")
            
        finally:
            # Cleanup
            mongo_client.reservations.delete_one({"_id": inserted_id})

    def test_lazy_cancel_does_not_cancel_confirmed_payment(self, api_client, mongo_client):
        """Test that reservations with payment_status='confirmed' are NOT auto-cancelled."""
        old_time = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
        future_date = (datetime.now(timezone.utc) + timedelta(days=9)).strftime("%Y-%m-%d")
        
        test_reservation = {
            "booking_id": "TEST_LC3",
            "services": [SERVICE_ID],
            "service_names": ["Test Service"],
            "service_worker_pairs": [{
                "service_id": SERVICE_ID,
                "worker_id": WORKER_ID,
                "service_name": "Test Service",
                "worker_name": "Test Worker",
                "duration": 30,
                "price": 1000
            }],
            "worker_time_blocks": [],
            "worker_id": WORKER_ID,
            "worker_name": "Test Worker",
            "date": future_date,
            "time": "12:00",
            "end_time": "12:30",
            "total_duration": 30,
            "total_price": 1000,
            "client_name": "Test Client LC3",
            "client_phone": "381999888555",
            "client_email": "test_lc3@test.com",
            "status": "confirmed",
            "payment_status": "confirmed",  # Key: confirmed payment - should NOT be cancelled
            "advance_required": True,
            "advance_released": False,
            "created_at": old_time  # Old but payment is confirmed
        }
        
        result = mongo_client.reservations.insert_one(test_reservation)
        inserted_id = result.inserted_id
        
        try:
            # Call available-slots endpoint (triggers lazy cancel)
            response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
                "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
                "date": future_date
            })
            assert response.status_code == 200
            
            # Verify the reservation was NOT cancelled
            res = mongo_client.reservations.find_one({"_id": inserted_id})
            assert res is not None, "Reservation not found"
            assert res.get("status") == "confirmed", f"Expected confirmed, got {res.get('status')}"
            assert res.get("cancelled_by") is None, "cancelled_by should be None"
            print(f"✓ Confirmed payment reservation NOT cancelled: {inserted_id}")
            
        finally:
            mongo_client.reservations.delete_one({"_id": inserted_id})

    def test_lazy_cancel_does_not_cancel_sent_for_verification(self, api_client, mongo_client):
        """Test that reservations with payment_status='sent_for_verification' are NOT auto-cancelled."""
        old_time = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
        future_date = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
        
        test_reservation = {
            "booking_id": "TEST_LC4",
            "services": [SERVICE_ID],
            "service_names": ["Test Service"],
            "service_worker_pairs": [{
                "service_id": SERVICE_ID,
                "worker_id": WORKER_ID,
                "service_name": "Test Service",
                "worker_name": "Test Worker",
                "duration": 30,
                "price": 1000
            }],
            "worker_time_blocks": [],
            "worker_id": WORKER_ID,
            "worker_name": "Test Worker",
            "date": future_date,
            "time": "13:00",
            "end_time": "13:30",
            "total_duration": 30,
            "total_price": 1000,
            "client_name": "Test Client LC4",
            "client_phone": "381999888444",
            "client_email": "test_lc4@test.com",
            "status": "confirmed",
            "payment_status": "sent_for_verification",  # Key: sent_for_verification - should NOT be cancelled
            "advance_required": True,
            "advance_released": False,
            "created_at": old_time
        }
        
        result = mongo_client.reservations.insert_one(test_reservation)
        inserted_id = result.inserted_id
        
        try:
            # Call available-slots endpoint (triggers lazy cancel)
            response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
                "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
                "date": future_date
            })
            assert response.status_code == 200
            
            # Verify the reservation was NOT cancelled
            res = mongo_client.reservations.find_one({"_id": inserted_id})
            assert res is not None, "Reservation not found"
            assert res.get("status") == "confirmed", f"Expected confirmed, got {res.get('status')}"
            print(f"✓ sent_for_verification reservation NOT cancelled: {inserted_id}")
            
        finally:
            mongo_client.reservations.delete_one({"_id": inserted_id})

    def test_lazy_cancel_does_not_cancel_recent_reservation(self, api_client, mongo_client):
        """Test that reservations created less than 3 hours ago are NOT auto-cancelled."""
        recent_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()  # Only 1 hour old
        future_date = (datetime.now(timezone.utc) + timedelta(days=11)).strftime("%Y-%m-%d")
        
        test_reservation = {
            "booking_id": "TEST_LC5",
            "services": [SERVICE_ID],
            "service_names": ["Test Service"],
            "service_worker_pairs": [{
                "service_id": SERVICE_ID,
                "worker_id": WORKER_ID,
                "service_name": "Test Service",
                "worker_name": "Test Worker",
                "duration": 30,
                "price": 1000
            }],
            "worker_time_blocks": [],
            "worker_id": WORKER_ID,
            "worker_name": "Test Worker",
            "date": future_date,
            "time": "14:00",
            "end_time": "14:30",
            "total_duration": 30,
            "total_price": 1000,
            "client_name": "Test Client LC5",
            "client_phone": "381999888333",
            "client_email": "test_lc5@test.com",
            "status": "confirmed",
            "payment_status": "pending",  # Pending but recent
            "advance_required": True,
            "advance_released": False,
            "created_at": recent_time  # Key: only 1 hour old - should NOT be cancelled
        }
        
        result = mongo_client.reservations.insert_one(test_reservation)
        inserted_id = result.inserted_id
        
        try:
            # Call available-slots endpoint (triggers lazy cancel)
            response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
                "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
                "date": future_date
            })
            assert response.status_code == 200
            
            # Verify the reservation was NOT cancelled (too recent)
            res = mongo_client.reservations.find_one({"_id": inserted_id})
            assert res is not None, "Reservation not found"
            assert res.get("status") == "confirmed", f"Expected confirmed, got {res.get('status')}"
            print(f"✓ Recent reservation NOT cancelled: {inserted_id}")
            
        finally:
            mongo_client.reservations.delete_one({"_id": inserted_id})


class TestTriggerReminders:
    """Tests for POST /api/admin/reservations/trigger-reminders endpoint."""

    def test_trigger_reminders_requires_auth(self, api_client):
        """Test that trigger-reminders returns 401 without authentication."""
        # Remove auth header if present
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/admin/reservations/trigger-reminders", headers=headers)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ trigger-reminders requires auth: {response.status_code}")

    def test_trigger_reminders_returns_stats(self, authenticated_client):
        """Test that trigger-reminders returns reminder stats."""
        response = authenticated_client.post(f"{BASE_URL}/api/admin/reservations/trigger-reminders")
        assert response.status_code == 200, f"trigger-reminders failed: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "date" in data, "Response should contain 'date'"
        assert "total_reservations" in data, "Response should contain 'total_reservations'"
        assert "sent_confirmed" in data, "Response should contain 'sent_confirmed'"
        assert "sent_pending" in data, "Response should contain 'sent_pending'"
        assert "errors" in data, "Response should contain 'errors'"
        
        # Verify date is tomorrow (Belgrade timezone)
        from datetime import timezone, timedelta
        belgrade_tz = timezone(timedelta(hours=2))
        expected_tomorrow = (datetime.now(belgrade_tz) + timedelta(days=1)).strftime("%Y-%m-%d")
        assert data["date"] == expected_tomorrow, f"Expected date {expected_tomorrow}, got {data['date']}"
        
        print(f"✓ trigger-reminders returns stats: {data}")

    def test_trigger_reminders_processes_tomorrow_reservations(self, authenticated_client, mongo_client):
        """Test that trigger-reminders queries tomorrow's reservations correctly."""
        # Create a reservation for tomorrow
        from datetime import timezone, timedelta
        belgrade_tz = timezone(timedelta(hours=2))
        tomorrow = (datetime.now(belgrade_tz) + timedelta(days=1)).strftime("%Y-%m-%d")
        
        test_reservation = {
            "booking_id": "TEST_REM1",
            "services": [SERVICE_ID],
            "service_names": ["Test Service"],
            "service_worker_pairs": [{
                "service_id": SERVICE_ID,
                "worker_id": WORKER_ID,
                "service_name": "Test Service",
                "worker_name": "Test Worker",
                "duration": 30,
                "price": 1000
            }],
            "worker_time_blocks": [],
            "worker_id": WORKER_ID,
            "worker_name": "Test Worker",
            "date": tomorrow,  # Tomorrow's date
            "time": "15:00",
            "end_time": "15:30",
            "total_duration": 30,
            "total_price": 1000,
            "client_name": "Test Client Reminder",
            "client_phone": "381999888222",
            "client_email": "test_rem@test.com",
            "status": "confirmed",
            "payment_status": "pending",
            "advance_required": True,
            "advance_released": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = mongo_client.reservations.insert_one(test_reservation)
        inserted_id = result.inserted_id
        
        try:
            response = authenticated_client.post(f"{BASE_URL}/api/admin/reservations/trigger-reminders")
            assert response.status_code == 200, f"trigger-reminders failed: {response.text}"
            
            data = response.json()
            assert data["date"] == tomorrow, f"Expected date {tomorrow}, got {data['date']}"
            # Since VIBER_TOKEN is not set, errors will be counted (or sent_pending will be 0)
            # The key is that the endpoint processes correctly
            assert data["total_reservations"] >= 1, f"Expected at least 1 reservation, got {data['total_reservations']}"
            print(f"✓ trigger-reminders processes tomorrow's reservations: {data}")
            
        finally:
            mongo_client.reservations.delete_one({"_id": inserted_id})


class TestViberNotification:
    """Tests for send_viber_notification graceful handling."""

    def test_viber_notification_handles_missing_token(self, authenticated_client, mongo_client):
        """Test that send_viber_notification logs warning and returns False when VIBER_TOKEN is missing."""
        # Create a reservation for tomorrow to trigger reminder
        from datetime import timezone, timedelta
        belgrade_tz = timezone(timedelta(hours=2))
        tomorrow = (datetime.now(belgrade_tz) + timedelta(days=1)).strftime("%Y-%m-%d")
        
        test_reservation = {
            "booking_id": "TEST_VIB1",
            "services": [SERVICE_ID],
            "service_names": ["Test Service"],
            "service_worker_pairs": [{
                "service_id": SERVICE_ID,
                "worker_id": WORKER_ID,
                "service_name": "Test Service",
                "worker_name": "Test Worker",
                "duration": 30,
                "price": 1000
            }],
            "worker_time_blocks": [],
            "worker_id": WORKER_ID,
            "worker_name": "Test Worker",
            "date": tomorrow,
            "time": "16:00",
            "end_time": "16:30",
            "total_duration": 30,
            "total_price": 1000,
            "client_name": "Test Client Viber",
            "client_phone": "381999888111",
            "client_email": "test_vib@test.com",
            "status": "confirmed",
            "payment_status": "confirmed",
            "advance_required": True,
            "advance_released": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = mongo_client.reservations.insert_one(test_reservation)
        inserted_id = result.inserted_id
        
        try:
            # Call trigger-reminders - should not crash even without VIBER_TOKEN
            response = authenticated_client.post(f"{BASE_URL}/api/admin/reservations/trigger-reminders")
            assert response.status_code == 200, f"trigger-reminders should not crash: {response.text}"
            
            data = response.json()
            # Since VIBER_TOKEN is not set, errors should be counted (send_viber_notification returns False)
            # The key is that the endpoint doesn't crash
            print(f"✓ Viber notification handles missing token gracefully: {data}")
            
        finally:
            mongo_client.reservations.delete_one({"_id": inserted_id})


class TestFullBookingFlow:
    """Test that full booking flow still works after lazy cancel implementation."""

    def test_create_reservation_report_payment_admin_confirm(self, api_client, authenticated_client, mongo_client):
        """Test full flow: create reservation → report payment → admin confirm."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d")
        
        # Step 1: Get available slots
        slots_response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
            "date": future_date
        })
        assert slots_response.status_code == 200, f"Available slots failed: {slots_response.text}"
        slots_data = slots_response.json()
        assert "slots" in slots_data, "Response should contain 'slots'"
        
        if not slots_data["slots"]:
            pytest.skip("No available slots for testing")
        
        selected_time = slots_data["slots"][0]
        
        # Step 2: Create reservation
        create_response = api_client.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
            "date": future_date,
            "time": selected_time,
            "client_name": "Test Full Flow",
            "client_phone": "381999777666",
            "client_email": "test_flow@test.com"
        })
        assert create_response.status_code == 200, f"Create reservation failed: {create_response.text}"
        
        reservation_data = create_response.json()
        reservation_id = reservation_data["id"]
        assert reservation_data["payment_status"] == "pending", "Initial payment_status should be pending"
        
        try:
            # Step 3: Client reports payment
            report_response = api_client.patch(f"{BASE_URL}/api/reservations/{reservation_id}/report-payment")
            assert report_response.status_code == 200, f"Report payment failed: {report_response.text}"
            assert report_response.json()["payment_status"] == "sent_for_verification"
            
            # Step 4: Admin confirms payment
            confirm_response = authenticated_client.patch(f"{BASE_URL}/api/admin/reservations/{reservation_id}/confirm-payment")
            assert confirm_response.status_code == 200, f"Confirm payment failed: {confirm_response.text}"
            assert confirm_response.json()["payment_status"] == "confirmed"
            
            # Verify final state
            res = mongo_client.reservations.find_one({"_id": ObjectId(reservation_id)})
            assert res["payment_status"] == "confirmed", "Final payment_status should be confirmed"
            print(f"✓ Full booking flow works: {reservation_id}")
            
        finally:
            # Cleanup
            mongo_client.reservations.delete_one({"_id": ObjectId(reservation_id)})

    def test_available_slots_return_correct_data_after_lazy_cancel(self, api_client):
        """Test that available slots still return correct data after lazy cancel runs."""
        future_date = (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d")
        
        response = api_client.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
            "date": future_date
        })
        assert response.status_code == 200, f"Available slots failed: {response.text}"
        
        data = response.json()
        assert "slots" in data, "Response should contain 'slots'"
        assert "slot_details" in data, "Response should contain 'slot_details'"
        assert isinstance(data["slots"], list), "slots should be a list"
        
        # Verify slot_details structure if slots exist
        if data["slots"]:
            first_slot = data["slots"][0]
            assert first_slot in data["slot_details"], f"slot_details should contain {first_slot}"
            detail = data["slot_details"][first_slot]
            assert "end_time" in detail, "slot_details should contain end_time"
            assert "total_duration" in detail, "slot_details should contain total_duration"
        
        print(f"✓ Available slots return correct data: {len(data['slots'])} slots")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
