import requests
import sys
from datetime import datetime, timedelta
import json

class FocusedSalonTester:
    def __init__(self, base_url="https://slot-reserve-23.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

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
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def login_admin(self):
        """Login as admin"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@salon.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def get_services_and_workers(self):
        """Get existing services and workers"""
        services_success, services = self.run_test("Get Services", "GET", "services", 200)
        workers_success, workers = self.run_test("Get Workers", "GET", "workers", 200)
        
        if services_success and workers_success and services and workers:
            return services[0]['id'], workers[0]['id']
        return None, None

    def test_phone_normalization_blacklist(self):
        """Test that phone normalization works for blacklist"""
        print("\n" + "="*60)
        print("TESTING PHONE NORMALIZATION FOR BLACKLIST")
        print("="*60)
        
        service_id, worker_id = self.get_services_and_workers()
        if not service_id or not worker_id:
            print("❌ No services or workers available")
            return False
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Test different phone formats that should normalize to the same number
        phone_formats = [
            "+381611111111",
            "381611111111", 
            "0611111111",
            "611111111",
            "+381 61 111 1111",
            "061-111-1111"
        ]
        
        # First, add one format to blacklist
        blacklist_success, _ = self.run_test(
            "Add Phone to Blacklist",
            "POST",
            f"blacklist?phone={phone_formats[0]}",
            200
        )
        
        if not blacklist_success:
            return False
        
        # Now test that all formats are blocked
        all_blocked = True
        for i, phone in enumerate(phone_formats):
            reservation_data = {
                "services": [service_id],
                "worker_id": worker_id,
                "date": tomorrow,
                "time": f"{10 + i}:00",
                "client_name": f"Test User {i}",
                "client_phone": phone
            }
            
            success, _ = self.run_test(
                f"Blacklist Test - Format {i+1}: {phone}",
                "POST",
                "reservations",
                403,
                data=reservation_data
            )
            
            if not success:
                all_blocked = False
                print(f"   ❌ Phone format {phone} was not blocked!")
        
        # Clean up - remove from blacklist
        normalized_phone = ''.join(c for c in phone_formats[0] if c.isdigit())
        self.run_test(
            "Remove from Blacklist",
            "DELETE",
            f"blacklist/{normalized_phone}",
            200
        )
        
        return all_blocked

    def test_daily_limit_with_normalization(self):
        """Test max 3 reservations per day with phone normalization"""
        print("\n" + "="*60)
        print("TESTING DAILY LIMIT WITH PHONE NORMALIZATION")
        print("="*60)
        
        service_id, worker_id = self.get_services_and_workers()
        if not service_id or not worker_id:
            print("❌ No services or workers available")
            return False
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Use different phone formats but same normalized number
        phone_formats = [
            "+381622222222",  # 1st reservation
            "381622222222",   # 2nd reservation  
            "062-222-2222",   # 3rd reservation
            "+381 62 222 2222" # 4th reservation - should fail
        ]
        
        successful_bookings = 0
        
        for i, phone in enumerate(phone_formats):
            reservation_data = {
                "services": [service_id],
                "worker_id": worker_id,
                "date": tomorrow,
                "time": f"{16 + i}:00",
                "client_name": f"Daily Limit Test {i+1}",
                "client_phone": phone
            }
            
            expected_status = 200 if i < 3 else 400
            success, response = self.run_test(
                f"Daily Limit Test {i+1}/4 - {phone}",
                "POST",
                "reservations",
                expected_status,
                data=reservation_data
            )
            
            if success and expected_status == 200:
                successful_bookings += 1
                print(f"   ✅ Reservation {i+1} created successfully")
            elif success and expected_status == 400:
                print(f"   ✅ 4th reservation correctly rejected (daily limit reached)")
                return True
            else:
                print(f"   ❌ Unexpected result for reservation {i+1}")
        
        print(f"   ❌ Daily limit not enforced - created {successful_bookings} reservations")
        return False

    def test_admin_dashboard_reservations(self):
        """Test that admin can see reservations for selected date"""
        print("\n" + "="*60)
        print("TESTING ADMIN DASHBOARD RESERVATIONS")
        print("="*60)
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        success, response = self.run_test(
            f"Get Reservations for {tomorrow}",
            "GET",
            f"reservations?date={tomorrow}",
            200
        )
        
        if success:
            reservations = response
            print(f"   Found {len(reservations)} reservations for {tomorrow}")
            
            if reservations:
                print("   Reservation details:")
                for res in reservations[:5]:  # Show first 5
                    print(f"   - {res.get('time')} | {res.get('client_name')} | {res.get('client_phone')} | {res.get('total_price')} RSD")
                return True
            else:
                print("   ❌ No reservations found - this might be a filtering issue")
                return False
        
        return False

def main():
    print("🎯 FOCUSED SALON BOOKING TESTS")
    print("Testing: Blacklist, Daily Limits, Admin Dashboard")
    print("="*60)
    
    tester = FocusedSalonTester()
    
    # Login first
    if not tester.login_admin():
        print("❌ Failed to login as admin")
        return 1
    
    # Run focused tests
    tests = [
        ("Phone Normalization + Blacklist", tester.test_phone_normalization_blacklist),
        ("Daily Limit + Phone Normalization", tester.test_daily_limit_with_normalization),
        ("Admin Dashboard Reservations", tester.test_admin_dashboard_reservations),
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        test_func()
    
    # Print results
    print("\n" + "="*60)
    print("📊 FOCUSED TEST RESULTS")
    print("="*60)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())