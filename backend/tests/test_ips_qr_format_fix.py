"""
Test IPS QR Code Format Fix - Iteration 27
Tests that IPS amount uses dot decimal (RSD2000.00) instead of comma (RSD2000,00)
per NBS (National Bank of Serbia) standard for mBanking apps.
"""
import pytest
import requests
import os
import sys
import inspect

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestIPSAmountFormat:
    """Test IPS amount format uses dot decimal (NBS standard)"""
    
    def test_format_ips_amount_uses_dot_decimal(self):
        """format_ips_amount should return RSD2000.00 (dot), not RSD2000,00 (comma)"""
        from logic import format_ips_amount
        
        # Test various amounts
        assert format_ips_amount(2000) == "RSD2000.00", "Amount 2000 should be RSD2000.00"
        assert format_ips_amount(1500.50) == "RSD1500.50", "Amount 1500.50 should be RSD1500.50"
        assert format_ips_amount(0) == "RSD0.00", "Amount 0 should be RSD0.00"
        assert format_ips_amount(99.99) == "RSD99.99", "Amount 99.99 should be RSD99.99"
        assert format_ips_amount(10000) == "RSD10000.00", "Amount 10000 should be RSD10000.00"
        
        # Verify NO comma is present
        result = format_ips_amount(2000)
        assert ',' not in result, f"Amount should NOT contain comma, got: {result}"
        assert '.' in result, f"Amount should contain dot, got: {result}"
        print(f"✓ format_ips_amount(2000) = {result}")
    
    def test_format_ips_amount_two_decimal_places(self):
        """format_ips_amount should always have exactly 2 decimal places"""
        from logic import format_ips_amount
        
        # Integer amounts should have .00
        result = format_ips_amount(1000)
        assert result.endswith(".00"), f"Integer amount should end with .00, got: {result}"
        
        # Single decimal should be padded
        result = format_ips_amount(1000.5)
        assert result == "RSD1000.50", f"Single decimal should be padded, got: {result}"
        
        print("✓ format_ips_amount always returns 2 decimal places")


class TestIPSQRString:
    """Test IPS QR string generation with correct NBS format"""
    
    def test_generate_ips_qr_string_structure(self):
        """QR string should have correct NBS structure with dot decimal"""
        from logic import generate_ips_qr_string
        
        qr_string = generate_ips_qr_string(
            bank_account="160-0000000012345-67",
            recipient_name="Test Salon",
            amount=2000.00,
            booking_id="ABCD"
        )
        
        # Check structure
        lines = qr_string.split('\n')
        assert lines[0] == "K:PR", f"First line should be K:PR, got: {lines[0]}"
        assert lines[1] == "V:01", f"Second line should be V:01, got: {lines[1]}"
        assert lines[2] == "C:1", f"Third line should be C:1, got: {lines[2]}"
        
        # Find amount line (I:RSD...)
        amount_line = [l for l in lines if l.startswith("I:")]
        assert len(amount_line) == 1, "Should have exactly one amount line"
        assert amount_line[0] == "I:RSD2000.00", f"Amount line should be I:RSD2000.00, got: {amount_line[0]}"
        
        # Verify NO comma in amount
        assert "I:RSD2000,00" not in qr_string, "QR string should NOT contain comma decimal"
        
        print(f"✓ QR string amount line: {amount_line[0]}")
    
    def test_generate_ips_qr_string_all_fields(self):
        """QR string should contain all required NBS fields"""
        from logic import generate_ips_qr_string
        
        qr_string = generate_ips_qr_string(
            bank_account="160-0000000012345-67",
            recipient_name="Beauty Salon Bor",
            amount=1500.50,
            booking_id="XY12"
        )
        
        # Required fields per NBS standard
        assert "K:PR" in qr_string, "Missing K:PR (payment type)"
        assert "V:01" in qr_string, "Missing V:01 (version)"
        assert "C:1" in qr_string, "Missing C:1 (character set)"
        assert "R:" in qr_string, "Missing R: (bank account)"
        assert "N:" in qr_string, "Missing N: (recipient name)"
        assert "I:RSD1500.50" in qr_string, "Missing or incorrect I: (amount)"
        assert "SF:289" in qr_string, "Missing SF:289 (payment code)"
        assert "S:" in qr_string, "Missing S: (purpose)"
        assert "RO:99XY12" in qr_string, "Missing or incorrect RO: (reference)"
        
        print("✓ QR string contains all required NBS fields")
    
    def test_generate_ips_qr_string_serbian_transliteration(self):
        """QR string should transliterate Serbian characters"""
        from logic import generate_ips_qr_string
        
        qr_string = generate_ips_qr_string(
            bank_account="160-0000000012345-67",
            recipient_name="Šljivović Čedomir",  # Serbian chars
            amount=500,
            booking_id="TEST"
        )
        
        # Should be transliterated to uppercase ASCII
        assert "SLJIVOVIC CEDOMIR" in qr_string, "Serbian chars should be transliterated"
        assert "Š" not in qr_string, "Should not contain Š"
        assert "Č" not in qr_string, "Should not contain Č"
        
        print("✓ Serbian characters correctly transliterated")


class TestIPSQRImage:
    """Test IPS QR image generation"""
    
    def test_generate_ips_qr_image_returns_png(self):
        """generate_ips_qr_image should return valid PNG bytes"""
        from logic import generate_ips_qr_image
        
        qr_bytes = generate_ips_qr_image(
            bank_account="160-0000000012345-67",
            recipient_name="Test Salon",
            amount=2000,
            booking_id="ABCD"
        )
        
        # Check it's bytes
        assert isinstance(qr_bytes, bytes), "Should return bytes"
        
        # Check PNG magic bytes
        assert qr_bytes[:8] == b'\x89PNG\r\n\x1a\n', "Should be valid PNG format"
        
        # Check reasonable size (should be > 1KB for a QR code)
        assert len(qr_bytes) > 1000, f"QR image too small: {len(qr_bytes)} bytes"
        
        print(f"✓ QR image generated: {len(qr_bytes)} bytes")


class TestMailServiceAsync:
    """Test mail_service.py async function signature"""
    
    def test_send_booking_confirmation_email_is_async(self):
        """send_booking_confirmation_email should be an async function"""
        from mail_service import send_booking_confirmation_email
        
        # Check if it's a coroutine function
        assert inspect.iscoroutinefunction(send_booking_confirmation_email), \
            "send_booking_confirmation_email should be async (coroutine function)"
        
        print("✓ send_booking_confirmation_email is async")
    
    def test_mail_service_uses_format_ips_amount(self):
        """mail_service should use format_ips_amount for email HTML"""
        from mail_service import _build_html, format_ips_amount
        
        # Build HTML with test data
        html = _build_html(
            salon_name="Test Salon",
            booking_id="ABCD",
            client_name="Test Client",
            date="2026-01-15",
            time="10:00",
            end_time="11:00",
            service_lines=[{"service_name": "Haircut", "worker_name": "Ana"}],
            total_price=2000,
            total_duration=60,
            bank_account="160-0000000012345-67",
            payment_recipient="Test Salon"
        )
        
        # Check amount format in HTML
        expected_amount = format_ips_amount(2000)  # RSD2000.00
        assert expected_amount in html, f"HTML should contain {expected_amount}"
        assert "RSD2000,00" not in html, "HTML should NOT contain comma decimal"
        
        print(f"✓ Email HTML uses correct amount format: {expected_amount}")


class TestReservationAPIWithIPS:
    """Test POST /api/reservations triggers email with correct IPS format"""
    
    def test_reservations_endpoint_exists(self):
        """POST /api/reservations endpoint should exist"""
        # Just check the endpoint responds (even if validation fails)
        response = requests.post(
            f"{BASE_URL}/api/reservations",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        # Should get 422 (validation error) not 404
        assert response.status_code != 404, "POST /api/reservations endpoint should exist"
        print(f"✓ POST /api/reservations exists (status: {response.status_code})")


class TestCleanBankAccount:
    """Test bank account cleaning function"""
    
    def test_clean_bank_account_removes_formatting(self):
        """clean_bank_account should remove spaces and dashes"""
        from logic import clean_bank_account
        
        # With dashes
        result = clean_bank_account("160-0000000012345-67")
        assert "-" not in result, "Should remove dashes"
        assert " " not in result, "Should remove spaces"
        assert len(result) == 18, f"Should be 18 chars, got {len(result)}"
        
        # With spaces
        result = clean_bank_account("160 0000000012345 67")
        assert " " not in result, "Should remove spaces"
        
        print("✓ clean_bank_account removes formatting correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
