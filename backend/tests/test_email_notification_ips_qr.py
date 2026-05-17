"""
Test suite for Email Notification with IPS QR Code feature
Tests:
1. Backend: POST /api/reservations returns success even without SMTP config
2. Backend: Background email task runs without crashing (check logs)
3. Backend: Reservation created with all fields including client_email
4. Backend: logic.py transliterate_serbian correctly maps Serbian chars
5. Backend: logic.py generate_ips_qr_string produces NBS-compliant format
6. Backend: logic.py generate_ips_qr_image returns valid PNG bytes
7. Backend: mail_service.py handles missing SMTP gracefully
8. Backend: mail_service.py _build_html generates valid HTML with CID
9. Backend: Admin booking (POST /api/admin/reservations) works without email
"""

import pytest
import requests
import os
import sys
import time

# Load environment variables from backend .env
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://slot-reserve-23.preview.emergentagent.com').rstrip('/')

# Test data
SERVICE_ID = "69d549f035e38a4c2c9f0226"
WORKER_ID = "69d54b0635e38a4c2c9f022e"
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"


class TestIPSQRFunctions:
    """Test IPS QR code generation functions in logic.py"""
    
    def test_transliterate_serbian_basic(self):
        """Test Serbian character transliteration"""
        from logic import transliterate_serbian
        
        # Test basic Serbian characters
        assert transliterate_serbian("čćšžđ") == "CCSZDJ"
        assert transliterate_serbian("ČĆŠŽĐ") == "CCSZDJ"
        assert transliterate_serbian("Đorđe") == "DJORDJE"
        assert transliterate_serbian("Šljivovica") == "SLJIVOVICA"
        print("PASS: transliterate_serbian correctly maps Serbian chars to ASCII uppercase")
    
    def test_transliterate_serbian_mixed(self):
        """Test mixed text with Serbian and ASCII"""
        from logic import transliterate_serbian
        
        result = transliterate_serbian("Beauty Studio Bor")
        assert result == "BEAUTY STUDIO BOR"
        
        result = transliterate_serbian("Avans za rezervaciju ID ABC123")
        assert result == "AVANS ZA REZERVACIJU ID ABC123"
        print("PASS: transliterate_serbian handles mixed text correctly")
    
    def test_clean_bank_account(self):
        """Test bank account cleaning and formatting"""
        from logic import clean_bank_account
        
        # Test with dashes and spaces
        result = clean_bank_account("265-1234567890123-12")
        assert len(result) == 18
        assert result == "265123456789012312"
        
        # Test padding
        result = clean_bank_account("265")
        assert len(result) == 18
        assert result.startswith("265")
        print("PASS: clean_bank_account formats correctly")
    
    def test_format_ips_amount(self):
        """Test IPS amount formatting"""
        from logic import format_ips_amount
        
        result = format_ips_amount(1500.00)
        assert result == "RSD1500,00"
        
        result = format_ips_amount(12345.50)
        assert result == "RSD12345,50"
        print("PASS: format_ips_amount produces correct format")
    
    def test_generate_ips_qr_string_format(self):
        """Test IPS QR string generation - NBS compliant format with \\n delimiters"""
        from logic import generate_ips_qr_string
        
        qr_string = generate_ips_qr_string(
            bank_account="265-1234567890123-12",
            recipient_name="Beauty Studio Bor",
            amount=1500.00,
            booking_id="ABC1"
        )
        
        # Check it's a string with newline delimiters
        assert isinstance(qr_string, str)
        lines = qr_string.split('\n')
        
        # Verify NBS-compliant fields
        assert lines[0] == "K:PR"  # Payment request
        assert lines[1] == "V:01"  # Version
        assert lines[2] == "C:1"   # Character set
        assert lines[3].startswith("R:")  # Recipient account
        assert lines[4].startswith("N:")  # Recipient name
        assert lines[5].startswith("I:")  # Amount
        assert lines[6] == "SF:289"  # Payment code
        assert lines[7].startswith("S:")  # Purpose
        assert lines[8].startswith("RO:")  # Reference
        
        # Verify reference format
        assert "RO:99ABC1" in qr_string
        print("PASS: generate_ips_qr_string produces NBS-compliant format with \\n delimiters")
    
    def test_generate_ips_qr_image_returns_png(self):
        """Test IPS QR image generation returns valid PNG bytes"""
        from logic import generate_ips_qr_image
        
        image_bytes = generate_ips_qr_image(
            bank_account="265-1234567890123-12",
            recipient_name="Beauty Studio Bor",
            amount=1500.00,
            booking_id="TEST"
        )
        
        # Check it returns bytes
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        
        # Check PNG magic bytes
        assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        print("PASS: generate_ips_qr_image returns valid PNG bytes")


class TestMailService:
    """Test mail_service.py functions"""
    
    def test_smtp_config_returns_defaults(self):
        """Test _get_smtp_config returns defaults when env vars not set"""
        from mail_service import _get_smtp_config
        
        config = _get_smtp_config()
        assert "server" in config
        assert "port" in config
        assert "user" in config
        assert "password" in config
        # Without SMTP_USER/SMTP_PASSWORD, these should be empty
        # (graceful handling)
        print("PASS: _get_smtp_config returns config dict")
    
    def test_build_html_generates_valid_html(self):
        """Test _build_html generates valid HTML with CID image reference"""
        from mail_service import _build_html
        
        html = _build_html(
            salon_name="Beauty Studio Bor",
            booking_id="TEST",
            client_name="Test Client",
            date="2026-05-21",
            time="10:00",
            end_time="11:00",
            service_lines=[{"service_name": "Manikir", "worker_name": "Ana"}],
            total_price=1500.0,
            total_duration=60,
            bank_account="265-1234567890123-12",
            payment_recipient="Beauty Studio Bor"
        )
        
        # Check it's valid HTML
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        
        # Check CID image reference for QR code
        assert 'src="cid:qrcode_image"' in html or "src='cid:qrcode_image'" in html
        
        # Check dark theme elements
        assert "#0A0A0B" in html or "#141416" in html  # Dark background colors
        
        # Check booking details are present
        assert "TEST" in html  # booking_id
        assert "Test Client" in html
        assert "2026-05-21" in html
        assert "10:00" in html
        
        print("PASS: _build_html generates valid HTML with CID image reference")
    
    def test_send_email_handles_missing_smtp_gracefully(self):
        """Test send_booking_confirmation_email doesn't crash without SMTP"""
        from mail_service import send_booking_confirmation_email
        
        # This should NOT raise an exception even without SMTP credentials
        try:
            send_booking_confirmation_email(
                to_email="test@example.com",
                salon_name="Beauty Studio Bor",
                booking_id="TEST",
                client_name="Test Client",
                date="2026-05-21",
                time="10:00",
                end_time="11:00",
                service_worker_pairs=[{"service_name": "Manikir", "worker_name": "Ana"}],
                total_price=1500.0,
                total_duration=60,
                bank_account="265-1234567890123-12",
                payment_recipient="Beauty Studio Bor"
            )
            print("PASS: send_booking_confirmation_email handles missing SMTP gracefully (no crash)")
        except Exception as e:
            pytest.fail(f"send_booking_confirmation_email crashed: {e}")


class TestReservationEndpoints:
    """Test reservation API endpoints with email feature"""
    
    @pytest.fixture
    def session(self):
        """Create requests session"""
        return requests.Session()
    
    @pytest.fixture
    def auth_token(self, session):
        """Get admin auth token"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_get_available_slots(self, session):
        """Get available slots for testing"""
        # Get a future date
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        
        response = session.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_ID, "worker_id": WORKER_ID}
            ],
            "date": future_date
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        print(f"PASS: Got {len(data.get('slots', []))} available slots for {future_date}")
        return data.get("slots", []), future_date
    
    def test_create_reservation_with_email_returns_success(self, session):
        """Test POST /api/reservations returns success even without SMTP config"""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d")
        
        # Get available slots
        slots_response = session.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_ID, "worker_id": WORKER_ID}
            ],
            "date": future_date
        })
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots")
        
        test_time = slots[0]
        test_phone = f"0641234{datetime.now().strftime('%H%M%S')}"
        
        # Create reservation with email
        response = session.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_ID, "worker_id": WORKER_ID}
            ],
            "date": future_date,
            "time": test_time,
            "client_name": "TEST Email Notification",
            "client_phone": test_phone,
            "client_email": "test@example.com"
        })
        
        # Should return 200, NOT 500 (graceful email handling)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "booking_id" in data
        assert data.get("client_email") == "test@example.com"
        
        print(f"PASS: POST /api/reservations returns success (200) with booking_id={data['booking_id']}")
        print("PASS: Email failure does NOT cause 500 error")
    
    def test_reservation_contains_all_fields(self, session):
        """Test reservation response contains all required fields including client_email"""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Get available slots
        slots_response = session.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_ID, "worker_id": WORKER_ID}
            ],
            "date": future_date
        })
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots")
        
        test_time = slots[0]
        test_phone = f"0641235{datetime.now().strftime('%H%M%S')}"
        
        response = session.post(f"{BASE_URL}/api/reservations", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_ID, "worker_id": WORKER_ID}
            ],
            "date": future_date,
            "time": test_time,
            "client_name": "TEST All Fields",
            "client_phone": test_phone,
            "client_email": "AllFields@Example.COM"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        required_fields = [
            "id", "booking_id", "services", "service_names", 
            "service_worker_pairs", "date", "time", "end_time",
            "total_duration", "total_price", "client_name", 
            "client_phone", "client_email", "status", "payment_status"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check email is stored lowercase
        assert data["client_email"] == "allfields@example.com"
        
        print("PASS: Reservation created with all fields including client_email")
        print("PASS: Email stored as lowercase")
    
    def test_admin_reservation_without_email(self, session, auth_token):
        """Test POST /api/admin/reservations works without email field"""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        
        # Get available slots
        slots_response = session.post(f"{BASE_URL}/api/reservations/available-slots", json={
            "service_worker_pairs": [
                {"service_id": SERVICE_ID, "worker_id": WORKER_ID}
            ],
            "date": future_date
        })
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots")
        
        test_time = slots[0]
        test_phone = f"0641236{datetime.now().strftime('%H%M%S')}"
        
        # Admin booking WITHOUT email field
        response = session.post(
            f"{BASE_URL}/api/admin/reservations",
            json={
                "service_worker_pairs": [
                    {"service_id": SERVICE_ID, "worker_id": WORKER_ID}
                ],
                "date": future_date,
                "time": test_time,
                "client_name": "TEST Admin No Email",
                "client_phone": test_phone,
                "force": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "booking_id" in data
        # Admin booking should have empty client_email
        assert data.get("client_email") == ""
        
        print("PASS: Admin booking (POST /api/admin/reservations) works without email field")


class TestBackgroundEmailTask:
    """Test that background email task runs without crashing"""
    
    def test_background_task_logs_warning(self):
        """
        Verify background task runs and logs 'SMTP credentials not configured'
        This test checks the backend logs after creating a reservation
        """
        import subprocess
        
        # Check recent backend logs for the warning message
        result = subprocess.run(
            ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
            capture_output=True,
            text=True
        )
        
        log_content = result.stdout
        
        # The warning should appear in logs
        assert "SMTP credentials not configured" in log_content, \
            "Expected 'SMTP credentials not configured' warning in backend logs"
        
        print("PASS: Background email task runs and logs 'SMTP credentials not configured' warning")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
