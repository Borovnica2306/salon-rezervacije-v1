"""
Test Payment Tracking System
- PATCH /api/reservations/{id}/report-payment (client endpoint, no auth)
- PATCH /api/admin/reservations/{id}/confirm-payment (admin endpoint, requires auth)
- POST /api/my-reservations includes payment_status field
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"

# Test data from context
SERVICE_ID = "69d549f035e38a4c2c9f0226"
WORKER_ID = "69d54b0635e38a4c2c9f022e"


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
def test_reservation(admin_token):
    """Create a test reservation for payment tracking tests"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Use a future date to avoid time conflicts
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # Create reservation via admin endpoint
    payload = {
        "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
        "date": future_date,
        "time": "10:00",
        "client_name": "TEST_PaymentTracking",
        "client_phone": "+381641234567",
        "force": True
    }
    
    response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=headers)
    if response.status_code in [200, 201]:
        data = response.json()
        yield data
        # Cleanup: cancel the reservation
        requests.put(f"{BASE_URL}/api/reservations/{data['id']}/cancel", headers=headers)
    else:
        pytest.skip(f"Failed to create test reservation: {response.status_code} - {response.text}")


class TestClientReportPayment:
    """Tests for PATCH /api/reservations/{id}/report-payment (client endpoint)"""
    
    def test_report_payment_changes_status_to_sent_for_verification(self, test_reservation):
        """Client reports payment - status should change to sent_for_verification"""
        reservation_id = test_reservation["id"]
        
        response = requests.patch(f"{BASE_URL}/api/reservations/{reservation_id}/report-payment")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["payment_status"] == "sent_for_verification", f"Expected 'sent_for_verification', got {data['payment_status']}"
    
    def test_report_payment_returns_404_for_invalid_id(self):
        """Report payment with invalid ID should return 404"""
        invalid_id = "000000000000000000000000"  # Valid ObjectId format but doesn't exist
        
        response = requests.patch(f"{BASE_URL}/api/reservations/{invalid_id}/report-payment")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
    
    def test_report_payment_returns_400_if_already_confirmed(self, admin_token, test_reservation):
        """Report payment on already confirmed reservation should return 400"""
        reservation_id = test_reservation["id"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First, confirm the payment as admin
        confirm_response = requests.patch(
            f"{BASE_URL}/api/admin/reservations/{reservation_id}/confirm-payment",
            headers=headers
        )
        assert confirm_response.status_code == 200, f"Admin confirm failed: {confirm_response.text}"
        
        # Now try to report payment again as client
        response = requests.patch(f"{BASE_URL}/api/reservations/{reservation_id}/report-payment")
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "potvrđena" in response.json().get("detail", "").lower() or "confirmed" in response.json().get("detail", "").lower()


class TestAdminConfirmPayment:
    """Tests for PATCH /api/admin/reservations/{id}/confirm-payment (admin endpoint)"""
    
    def test_confirm_payment_requires_auth(self, test_reservation):
        """Admin confirm payment without auth should return 403"""
        reservation_id = test_reservation["id"]
        
        response = requests.patch(f"{BASE_URL}/api/admin/reservations/{reservation_id}/confirm-payment")
        
        # Should be 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}: {response.text}"
    
    def test_confirm_payment_changes_status_to_confirmed(self, admin_token):
        """Admin confirms payment - status should change to confirmed"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a fresh reservation for this test
        future_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
            "date": future_date,
            "time": "11:00",
            "client_name": "TEST_ConfirmPayment",
            "client_phone": "+381641234568",
            "force": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=headers)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        reservation_id = create_response.json()["id"]
        
        try:
            # First report payment as client
            report_response = requests.patch(f"{BASE_URL}/api/reservations/{reservation_id}/report-payment")
            assert report_response.status_code == 200, f"Report payment failed: {report_response.text}"
            
            # Then confirm as admin
            confirm_response = requests.patch(
                f"{BASE_URL}/api/admin/reservations/{reservation_id}/confirm-payment",
                headers=headers
            )
            
            assert confirm_response.status_code == 200, f"Expected 200, got {confirm_response.status_code}: {confirm_response.text}"
            data = confirm_response.json()
            assert data["payment_status"] == "confirmed", f"Expected 'confirmed', got {data['payment_status']}"
        finally:
            # Cleanup
            requests.put(f"{BASE_URL}/api/reservations/{reservation_id}/cancel", headers=headers)
    
    def test_confirm_payment_returns_404_for_invalid_id(self, admin_token):
        """Admin confirm payment with invalid ID should return 404"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        invalid_id = "000000000000000000000000"
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/reservations/{invalid_id}/confirm-payment",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestMyReservationsPaymentStatus:
    """Tests for POST /api/my-reservations including payment_status field"""
    
    def test_my_reservations_includes_payment_status(self, admin_token):
        """My reservations response should include payment_status field"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a reservation with a known phone
        future_date = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")
        test_phone = "+381641234569"
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
            "date": future_date,
            "time": "12:00",
            "client_name": "TEST_MyReservations",
            "client_phone": test_phone,
            "force": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=headers)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        reservation_id = create_response.json()["id"]
        
        try:
            # Fetch my reservations
            my_res_response = requests.post(f"{BASE_URL}/api/my-reservations", json={"phone": test_phone})
            
            assert my_res_response.status_code == 200, f"Expected 200, got {my_res_response.status_code}: {my_res_response.text}"
            reservations = my_res_response.json()
            
            assert len(reservations) > 0, "Expected at least one reservation"
            
            # Find our test reservation
            test_res = next((r for r in reservations if r["id"] == reservation_id), None)
            assert test_res is not None, "Test reservation not found in my-reservations"
            
            # Check payment_status field exists
            assert "payment_status" in test_res, "payment_status field missing from my-reservations response"
            assert test_res["payment_status"] == "pending", f"Expected 'pending', got {test_res['payment_status']}"
        finally:
            # Cleanup
            requests.put(f"{BASE_URL}/api/reservations/{reservation_id}/cancel", headers=headers)
    
    def test_my_reservations_shows_sent_for_verification_status(self, admin_token):
        """My reservations should show sent_for_verification after client reports payment"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a reservation
        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        test_phone = "+381641234570"
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
            "date": future_date,
            "time": "13:00",
            "client_name": "TEST_VerificationStatus",
            "client_phone": test_phone,
            "force": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=headers)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        reservation_id = create_response.json()["id"]
        
        try:
            # Report payment as client
            report_response = requests.patch(f"{BASE_URL}/api/reservations/{reservation_id}/report-payment")
            assert report_response.status_code == 200, f"Report payment failed: {report_response.text}"
            
            # Fetch my reservations
            my_res_response = requests.post(f"{BASE_URL}/api/my-reservations", json={"phone": test_phone})
            assert my_res_response.status_code == 200
            
            reservations = my_res_response.json()
            test_res = next((r for r in reservations if r["id"] == reservation_id), None)
            
            assert test_res is not None, "Test reservation not found"
            assert test_res["payment_status"] == "sent_for_verification", f"Expected 'sent_for_verification', got {test_res['payment_status']}"
        finally:
            # Cleanup
            requests.put(f"{BASE_URL}/api/reservations/{reservation_id}/cancel", headers=headers)
    
    def test_my_reservations_shows_confirmed_status(self, admin_token):
        """My reservations should show confirmed after admin confirms payment"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a reservation
        future_date = (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d")
        test_phone = "+381641234571"
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
            "date": future_date,
            "time": "14:00",
            "client_name": "TEST_ConfirmedStatus",
            "client_phone": test_phone,
            "force": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=headers)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        reservation_id = create_response.json()["id"]
        
        try:
            # Report payment as client
            requests.patch(f"{BASE_URL}/api/reservations/{reservation_id}/report-payment")
            
            # Confirm as admin
            confirm_response = requests.patch(
                f"{BASE_URL}/api/admin/reservations/{reservation_id}/confirm-payment",
                headers=headers
            )
            assert confirm_response.status_code == 200, f"Confirm failed: {confirm_response.text}"
            
            # Fetch my reservations
            my_res_response = requests.post(f"{BASE_URL}/api/my-reservations", json={"phone": test_phone})
            assert my_res_response.status_code == 200
            
            reservations = my_res_response.json()
            test_res = next((r for r in reservations if r["id"] == reservation_id), None)
            
            assert test_res is not None, "Test reservation not found"
            assert test_res["payment_status"] == "confirmed", f"Expected 'confirmed', got {test_res['payment_status']}"
        finally:
            # Cleanup
            requests.put(f"{BASE_URL}/api/reservations/{reservation_id}/cancel", headers=headers)


class TestAdminReservationsPaymentStatus:
    """Tests for GET /api/reservations (admin) including payment_status"""
    
    def test_admin_reservations_includes_payment_status(self, admin_token):
        """Admin reservations endpoint should include payment_status field"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create a reservation
        future_date = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
        payload = {
            "service_worker_pairs": [{"service_id": SERVICE_ID, "worker_id": WORKER_ID}],
            "date": future_date,
            "time": "15:00",
            "client_name": "TEST_AdminPaymentStatus",
            "client_phone": "+381641234572",
            "force": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/reservations", json=payload, headers=headers)
        assert create_response.status_code in [200, 201], f"Create failed: {create_response.text}"
        reservation_id = create_response.json()["id"]
        
        try:
            # Fetch admin reservations for that date
            res_response = requests.get(
                f"{BASE_URL}/api/reservations",
                params={"date": future_date},
                headers=headers
            )
            
            assert res_response.status_code == 200, f"Expected 200, got {res_response.status_code}"
            reservations = res_response.json()
            
            # Find our test reservation
            test_res = next((r for r in reservations if r["id"] == reservation_id), None)
            assert test_res is not None, "Test reservation not found in admin reservations"
            
            # Check payment_status field exists
            assert "payment_status" in test_res, "payment_status field missing from admin reservations response"
        finally:
            # Cleanup
            requests.put(f"{BASE_URL}/api/reservations/{reservation_id}/cancel", headers=headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
