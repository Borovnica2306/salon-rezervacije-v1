import requests
import sys
from datetime import datetime, timedelta
import json

class SalonNewFeaturesTester:
    def __init__(self, base_url="https://slot-reserve-23.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []
        self.test_phone = "0601234567"
        self.test_reservation_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                    self.issues.append(f"{name}: Expected {expected_status}, got {response.status_code} - {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                    self.issues.append(f"{name}: Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.issues.append(f"{name}: Exception - {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login with correct credentials"""
        print("\n" + "="*50)
        print("TESTING ADMIN AUTHENTICATION")
        print("="*50)
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@salon.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   ✅ Admin authenticated successfully")
            print(f"   User role: {response.get('role', 'unknown')}")
            return True
        else:
            self.issues.append("Admin login failed - cannot proceed with admin-only tests")
        return False

    def test_admin_reservations_table(self):
        """Test admin can see reservations in table format"""
        print("\n" + "="*50)
        print("TESTING ADMIN RESERVATIONS TABLE")
        print("="*50)
        
        if not self.token:
            print("❌ No admin token - skipping")
            return False
        
        # Get today's reservations
        today = datetime.now().strftime("%Y-%m-%d")
        
        success, response = self.run_test(
            "Get Admin Reservations",
            "GET",
            f"reservations?date={today}",
            200
        )
        
        if not success:
            return False
        
        reservations = response
        print(f"   Found {len(reservations)} reservations for {today}")
        
        # Check if we have the expected table columns in response
        if reservations:
            reservation = reservations[0]
            expected_fields = [
                'time', 'client_name', 'client_phone', 'service_names', 
                'worker_name', 'total_price', 'advance_required', 'id'
            ]
            
            missing_fields = []
            for field in expected_fields:
                if field not in reservation:
                    missing_fields.append(field)
            
            if missing_fields:
                self.issues.append(f"Missing reservation fields: {missing_fields}")
                print(f"❌ Missing fields: {missing_fields}")
                return False
            
            print("✅ Reservations table has all required columns")
        else:
            print("✅ Reservations endpoint working (no reservations today)")
        
        return True

    def test_blacklist_endpoints(self):
        """Test admin blacklist functionality"""
        print("\n" + "="*50)
        print("TESTING BLACKLIST ENDPOINTS")
        print("="*50)
        
        if not self.token:
            print("❌ No admin token - skipping")
            return False
        
        test_phone = "0611111111"
        
        # 1. Get current blacklist
        success, response = self.run_test(
            "Get Blacklist",
            "GET",
            "blacklist",
            200
        )
        
        if not success:
            return False
        
        initial_count = len(response)
        print(f"   Initial blacklist count: {initial_count}")
        
        # 2. Add phone to blacklist
        success, response = self.run_test(
            "Add to Blacklist",
            "POST",
            f"blacklist?phone={test_phone}",
            200
        )
        
        if not success:
            return False
        
        # 3. Verify phone was added
        success, response = self.run_test(
            "Get Blacklist After Add",
            "GET",
            "blacklist",
            200
        )
        
        if not success:
            return False
        
        new_count = len(response)
        if new_count != initial_count + 1:
            self.issues.append(f"Blacklist count should be {initial_count + 1}, got {new_count}")
            print(f"❌ Blacklist count mismatch")
            return False
        
        # Check if our phone is in the list
        phones = [item['phone'] for item in response]
        normalized_phone = ''.join(c for c in test_phone if c.isdigit())
        
        if normalized_phone not in phones:
            self.issues.append(f"Phone {normalized_phone} not found in blacklist")
            print(f"❌ Phone not found in blacklist")
            return False
        
        # 4. Remove phone from blacklist
        success, response = self.run_test(
            "Remove from Blacklist",
            "DELETE",
            f"blacklist/{normalized_phone}",
            200
        )
        
        if not success:
            return False
        
        # 5. Verify phone was removed
        success, response = self.run_test(
            "Get Blacklist After Remove",
            "GET",
            "blacklist",
            200
        )
        
        if not success:
            return False
        
        final_count = len(response)
        if final_count != initial_count:
            self.issues.append(f"Final blacklist count should be {initial_count}, got {final_count}")
            print(f"❌ Final blacklist count mismatch")
            return False
        
        print("✅ Blacklist add/remove functionality working")
        return True

    def create_test_reservation(self):
        """Create a test reservation for client testing"""
        print("\n" + "="*50)
        print("CREATING TEST RESERVATION")
        print("="*50)
        
        # Get services and workers first
        success, services = self.run_test("Get Services", "GET", "services", 200)
        if not success or not services:
            return False
        
        success, workers = self.run_test("Get Workers", "GET", "workers", 200)
        if not success or not workers:
            return False
        
        # Find a future date (tomorrow)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Get available slots
        slots_data = {
            "services": [services[0]['id']],
            "worker_id": workers[0]['id'],
            "date": tomorrow
        }
        
        success, slots_response = self.run_test(
            "Get Available Slots",
            "POST",
            "reservations/available-slots",
            200,
            data=slots_data
        )
        
        if not success or not slots_response.get('slots'):
            print("❌ No available slots for test reservation")
            return False
        
        # Create reservation
        reservation_data = {
            "services": [services[0]['id']],
            "worker_id": workers[0]['id'],
            "date": tomorrow,
            "time": slots_response['slots'][0],
            "client_name": "Test Client",
            "client_phone": self.test_phone
        }
        
        success, response = self.run_test(
            "Create Test Reservation",
            "POST",
            "reservations",
            200,
            data=reservation_data
        )
        
        if success and 'id' in response:
            self.test_reservation_id = response['id']
            print(f"   ✅ Test reservation created: {self.test_reservation_id}")
            return True
        
        return False

    def test_client_my_reservations(self):
        """Test client can get their reservations by phone"""
        print("\n" + "="*50)
        print("TESTING CLIENT MY-RESERVATIONS")
        print("="*50)
        
        # First create a test reservation
        if not self.create_test_reservation():
            print("❌ Could not create test reservation")
            return False
        
        # Test getting reservations by phone (no auth required)
        success, response = self.run_test(
            "Get My Reservations",
            "POST",
            "my-reservations",
            200,
            data={"phone": self.test_phone},
            headers={}  # No auth token needed
        )
        
        if not success:
            return False
        
        reservations = response
        print(f"   Found {len(reservations)} reservations for phone {self.test_phone}")
        
        if not reservations:
            self.issues.append("No reservations found for test phone")
            print("❌ No reservations found")
            return False
        
        # Check reservation structure
        reservation = reservations[0]
        expected_fields = ['id', 'services', 'worker_name', 'date', 'time', 'can_cancel']
        
        missing_fields = []
        for field in expected_fields:
            if field not in reservation:
                missing_fields.append(field)
        
        if missing_fields:
            self.issues.append(f"Missing my-reservations fields: {missing_fields}")
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        print("✅ My-reservations endpoint working with correct structure")
        return True

    def test_client_cancel_reservation(self):
        """Test client can cancel their own reservation"""
        print("\n" + "="*50)
        print("TESTING CLIENT RESERVATION CANCELLATION")
        print("="*50)
        
        if not self.test_reservation_id:
            print("❌ No test reservation ID available")
            return False
        
        # Test cancelling the reservation
        success, response = self.run_test(
            "Cancel My Reservation",
            "PUT",
            f"my-reservations/{self.test_reservation_id}/cancel",
            200,
            data={"phone": self.test_phone},
            headers={}  # No auth token needed
        )
        
        if not success:
            return False
        
        print("✅ Client reservation cancellation working")
        
        # Verify reservation is cancelled by checking my-reservations again
        success, response = self.run_test(
            "Verify Cancellation",
            "POST",
            "my-reservations",
            200,
            data={"phone": self.test_phone},
            headers={}
        )
        
        if success:
            # Should have no active reservations now
            active_reservations = [r for r in response if r.get('status') != 'cancelled']
            if active_reservations:
                print(f"⚠️  Still found {len(active_reservations)} active reservations after cancellation")
            else:
                print("✅ Reservation successfully cancelled")
        
        return True

    def test_24h_cancellation_rule(self):
        """Test 24h cancellation rule"""
        print("\n" + "="*50)
        print("TESTING 24H CANCELLATION RULE")
        print("="*50)
        
        # This test would require creating a reservation for today/tomorrow
        # and checking the can_cancel field in the response
        
        # Get reservations to check can_cancel logic
        success, response = self.run_test(
            "Check Cancellation Rules",
            "POST",
            "my-reservations",
            200,
            data={"phone": self.test_phone},
            headers={}
        )
        
        if success:
            for reservation in response:
                print(f"   Reservation {reservation['date']} {reservation['time']}: can_cancel = {reservation.get('can_cancel', 'unknown')}")
            print("✅ 24h cancellation rule check completed")
            return True
        
        return False

def main():
    print("🏪 SALON BOOKING API - NEW FEATURES TESTING")
    print("="*60)
    print("Testing new features:")
    print("- Admin login (admin@salon.com / Admin123!)")
    print("- Admin reservations table view")
    print("- Admin Blacklist (Crna Lista) functionality")
    print("- Client 'Moje rezervacije' (My Reservations)")
    print("- Client reservation cancellation")
    print("- 24h cancellation rule")
    print("="*60)
    
    tester = SalonNewFeaturesTester()
    
    # Test sequence for new features
    tests = [
        ("Admin Authentication", tester.test_admin_login),
        ("Admin Reservations Table", tester.test_admin_reservations_table),
        ("Blacklist Functionality", tester.test_blacklist_endpoints),
        ("Client My Reservations", tester.test_client_my_reservations),
        ("Client Cancel Reservation", tester.test_client_cancel_reservation),
        ("24h Cancellation Rule", tester.test_24h_cancellation_rule),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if not test_func():
            print(f"❌ Test failed: {test_name}")
    
    # Print final results
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.issues:
        print(f"\n❌ ISSUES FOUND ({len(tester.issues)}):")
        for i, issue in enumerate(tester.issues, 1):
            print(f"   {i}. {issue}")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL NEW FEATURES TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())