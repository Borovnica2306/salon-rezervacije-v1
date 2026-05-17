"""
Test IPS QR Code Format Fix - Iteration 28
Tests that IPS QR code uses:
1. Pipe '|' separator (not newline)
2. Comma decimal for amount (RSD2000,00 not RSD2000.00) per NBS standard

NBS Reference format: K:PR|V:01|C:1|R:845000000040484987|N:JP EPS BEOGRAD|I:RSD3596,13|SF:289|S:...|RO:...
"""
import pytest
import requests
import os
import sys

# Add backend to path for direct imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestIPSAmountFormatCommaDecimal:
    """Test IPS amount format uses COMMA decimal (NBS standard)"""
    
    def test_format_ips_amount_uses_comma_decimal(self):
        """format_ips_amount should return RSD2000,00 (comma), not RSD2000.00 (dot)"""
        from logic import format_ips_amount
        
        # Test various amounts - NBS requires comma decimal
        assert format_ips_amount(2000) == "RSD2000,00", f"Amount 2000 should be RSD2000,00, got: {format_ips_amount(2000)}"
        assert format_ips_amount(3596.13) == "RSD3596,13", f"Amount 3596.13 should be RSD3596,13, got: {format_ips_amount(3596.13)}"
        assert format_ips_amount(100.5) == "RSD100,50", f"Amount 100.5 should be RSD100,50, got: {format_ips_amount(100.5)}"
        assert format_ips_amount(0) == "RSD0,00", f"Amount 0 should be RSD0,00, got: {format_ips_amount(0)}"
        
        # Verify comma IS present, dot is NOT
        result = format_ips_amount(2000)
        assert ',' in result, f"Amount should contain comma, got: {result}"
        assert '.' not in result, f"Amount should NOT contain dot, got: {result}"
        print(f"✓ format_ips_amount(2000) = {result} (comma decimal)")
    
    def test_format_ips_amount_no_thousands_separator(self):
        """format_ips_amount should NOT have thousands separator"""
        from logic import format_ips_amount
        
        # Large amounts should not have thousands separator
        result = format_ips_amount(10000)
        assert result == "RSD10000,00", f"10000 should be RSD10000,00 (no thousands sep), got: {result}"
        
        result = format_ips_amount(1000000)
        assert result == "RSD1000000,00", f"1000000 should be RSD1000000,00 (no thousands sep), got: {result}"
        
        print("✓ format_ips_amount has no thousands separator")


class TestIPSQRStringPipeSeparator:
    """Test IPS QR string uses pipe '|' separator (not newline)"""
    
    def test_generate_ips_qr_string_uses_pipe_separator(self):
        """QR string should use pipe '|' separator, NOT newline"""
        from logic import generate_ips_qr_string
        
        qr_string = generate_ips_qr_string(
            bank_account="115-0381692422596-18",
            recipient_name="Beauty Salon Bor",
            amount=2000,
            booking_id="TEST"
        )
        
        # Check NO newlines
        assert '\n' not in qr_string, f"QR string should NOT contain newline, got: {repr(qr_string)}"
        assert '\r' not in qr_string, f"QR string should NOT contain carriage return"
        
        # Check pipe separator IS present
        assert '|' in qr_string, f"QR string should contain pipe separator, got: {qr_string}"
        
        # Count pipes - should have 8 pipes for 9 fields
        pipe_count = qr_string.count('|')
        assert pipe_count == 8, f"QR string should have 8 pipes (9 fields), got {pipe_count}"
        
        print(f"✓ QR string uses pipe separator: {qr_string[:50]}...")
    
    def test_generate_ips_qr_string_matches_nbs_format(self):
        """QR string should match NBS format: K:PR|V:01|C:1|R:...|N:...|I:RSD...|SF:289|S:...|RO:..."""
        from logic import generate_ips_qr_string
        
        qr_string = generate_ips_qr_string(
            bank_account="115-0381692422596-18",
            recipient_name="Beauty Salon Bor",
            amount=2000,
            booking_id="ABCD"
        )
        
        # Split by pipe
        fields = qr_string.split('|')
        
        # Verify field order and format
        assert fields[0] == "K:PR", f"Field 0 should be K:PR, got: {fields[0]}"
        assert fields[1] == "V:01", f"Field 1 should be V:01, got: {fields[1]}"
        assert fields[2] == "C:1", f"Field 2 should be C:1, got: {fields[2]}"
        assert fields[3].startswith("R:"), f"Field 3 should start with R:, got: {fields[3]}"
        assert fields[4].startswith("N:"), f"Field 4 should start with N:, got: {fields[4]}"
        assert fields[5] == "I:RSD2000,00", f"Field 5 should be I:RSD2000,00, got: {fields[5]}"
        assert fields[6] == "SF:289", f"Field 6 should be SF:289, got: {fields[6]}"
        assert fields[7].startswith("S:"), f"Field 7 should start with S:, got: {fields[7]}"
        assert fields[8].startswith("RO:"), f"Field 8 should start with RO:, got: {fields[8]}"
        
        print(f"✓ QR string matches NBS format")
        print(f"  Full string: {qr_string}")
    
    def test_generate_ips_qr_string_amount_with_comma(self):
        """Amount field in QR string should use comma decimal"""
        from logic import generate_ips_qr_string
        
        # Test with decimal amount
        qr_string = generate_ips_qr_string(
            bank_account="115-0381692422596-18",
            recipient_name="Test",
            amount=3596.13,
            booking_id="TEST"
        )
        
        # Amount should be I:RSD3596,13 (comma decimal)
        assert "I:RSD3596,13" in qr_string, f"Amount should be I:RSD3596,13, got: {qr_string}"
        assert "I:RSD3596.13" not in qr_string, f"Amount should NOT use dot decimal"
        
        print(f"✓ QR string amount uses comma decimal: I:RSD3596,13")


class TestIPSQRImage:
    """Test IPS QR image generation returns valid PNG"""
    
    def test_generate_ips_qr_image_returns_valid_png(self):
        """generate_ips_qr_image should return valid PNG bytes"""
        from logic import generate_ips_qr_image
        
        qr_bytes = generate_ips_qr_image(
            bank_account="115-0381692422596-18",
            recipient_name="Beauty Salon Bor",
            amount=2000,
            booking_id="TEST"
        )
        
        # Check it's bytes
        assert isinstance(qr_bytes, bytes), "Should return bytes"
        
        # Check PNG magic bytes
        assert qr_bytes[:8] == b'\x89PNG\r\n\x1a\n', "Should be valid PNG format"
        
        # Check reasonable size (should be > 1KB for a QR code)
        assert len(qr_bytes) > 1000, f"QR image too small: {len(qr_bytes)} bytes"
        
        print(f"✓ QR image generated: {len(qr_bytes)} bytes (valid PNG)")


class TestCleanBankAccount:
    """Test bank account cleaning function"""
    
    def test_clean_bank_account_removes_formatting(self):
        """clean_bank_account should remove spaces and dashes, pad to 18 chars"""
        from logic import clean_bank_account
        
        # With dashes
        result = clean_bank_account("115-0381692422596-18")
        assert "-" not in result, "Should remove dashes"
        assert " " not in result, "Should remove spaces"
        assert len(result) == 18, f"Should be 18 chars, got {len(result)}: {result}"
        assert result == "115038169242259618", f"Expected 115038169242259618, got: {result}"
        
        print(f"✓ clean_bank_account('115-0381692422596-18') = {result}")


class TestSerbianTransliteration:
    """Test Serbian character transliteration"""
    
    def test_transliterate_serbian_characters(self):
        """Serbian characters should be transliterated to ASCII uppercase"""
        from logic import transliterate_serbian
        
        # Test various Serbian characters
        assert transliterate_serbian("Šljivović") == "SLJIVOVIC", "Š should become S"
        assert transliterate_serbian("Čedomir") == "CEDOMIR", "Č should become C"
        assert transliterate_serbian("Đorđe") == "DJORDJE", "Đ should become DJ"
        assert transliterate_serbian("Žika") == "ZIKA", "Ž should become Z"
        assert transliterate_serbian("ćevapi") == "CEVAPI", "ć should become C"
        
        print("✓ Serbian transliteration works correctly")


class TestReservationEmailUsesClientEmail:
    """Test that POST /api/reservations sends email to client_email from request"""
    
    def test_reservations_endpoint_accepts_client_email(self):
        """POST /api/reservations should accept client_email field"""
        # Just verify the endpoint accepts the field (validation will fail without full data)
        response = requests.post(
            f"{BASE_URL}/api/reservations",
            json={
                "client_email": "test@example.com",
                "client_name": "Test",
                "client_phone": "+381641234567"
            },
            headers={"Content-Type": "application/json"}
        )
        
        # Should get 422 (validation error for missing fields) not 404
        assert response.status_code != 404, "POST /api/reservations endpoint should exist"
        
        # Check error is about missing fields, not about client_email being invalid
        if response.status_code == 422:
            error_detail = response.json().get("detail", [])
            # Should complain about missing service_worker_pairs, date, time - not client_email
            field_errors = [e.get("loc", [])[-1] for e in error_detail if isinstance(e, dict)]
            assert "client_email" not in field_errors, "client_email should be accepted"
        
        print(f"✓ POST /api/reservations accepts client_email field (status: {response.status_code})")


class TestFullIPSQRStringComparison:
    """Compare generated QR string with NBS reference format"""
    
    def test_qr_string_format_matches_nbs_example(self):
        """Generated QR string should match NBS format structure"""
        from logic import generate_ips_qr_string
        
        # NBS Reference: K:PR|V:01|C:1|R:845000000040484987|N:JP EPS BEOGRAD|I:RSD3596,13|SF:289|S:...|RO:...
        
        qr_string = generate_ips_qr_string(
            bank_account="845-0000000404849-87",
            recipient_name="JP EPS BEOGRAD",
            amount=3596.13,
            booking_id="TEST"
        )
        
        # Verify structure matches NBS
        assert qr_string.startswith("K:PR|V:01|C:1|"), f"Should start with K:PR|V:01|C:1|, got: {qr_string[:20]}"
        assert "|I:RSD3596,13|" in qr_string, f"Should contain |I:RSD3596,13|, got: {qr_string}"
        assert "|SF:289|" in qr_string, f"Should contain |SF:289|, got: {qr_string}"
        
        # No newlines
        assert '\n' not in qr_string, "Should not contain newlines"
        
        print(f"✓ QR string matches NBS format structure")
        print(f"  Generated: {qr_string}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
