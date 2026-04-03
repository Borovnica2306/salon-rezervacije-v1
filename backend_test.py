import requests
import sys
from datetime import datetime, timedelta
import json

class SalonAPITester:
    def __init__(self, base_url="https://slot-reserve-23.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_service_id = None
        self.created_worker_id = None
        self.created_reservation_id = None

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
        print(f"   URL: {method} {url}")
        
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
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login and get token"""
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
            print(f"   Token received: {self.token[:20]}...")
            return True
        return False

    def test_get_me(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        if success:
            print(f"   User: {response.get('email')} ({response.get('role')})")
        return success

    def test_create_service(self):
        """Create a service (Šišanje, 30min, 2000 RSD, category: hair)"""
        print("\n" + "="*50)
        print("TESTING SERVICE MANAGEMENT")
        print("="*50)
        
        service_data = {
            "name": "Šišanje",
            "category": "hair",
            "duration": 30,
            "price": 2000,
            "description": "Profesionalno šišanje"
        }
        
        success, response = self.run_test(
            "Create Service",
            "POST",
            "services",
            200,
            data=service_data
        )
        if success and 'id' in response:
            self.created_service_id = response['id']
            print(f"   Service created with ID: {self.created_service_id}")
            return True
        return False

    def test_get_services(self):
        """Get all services"""
        success, response = self.run_test(
            "Get Services",
            "GET",
            "services",
            200
        )
        if success:
            print(f"   Found {len(response)} services")
            for service in response:
                if service.get('name') == 'Šišanje':
                    print(f"   ✅ Found created service: {service['name']} - {service['price']} RSD")
        return success

    def test_create_worker(self):
        """Create a worker (Ana) assigned to the service"""
        print("\n" + "="*50)
        print("TESTING WORKER MANAGEMENT")
        print("="*50)
        
        if not self.created_service_id:
            print("❌ Cannot create worker - no service ID available")
            return False
            
        worker_data = {
            "name": "Ana",
            "services": [self.created_service_id],
            "work_start": "09:00",
            "work_end": "21:00",
            "break_start": "13:00",
            "break_end": "14:00",
            "days_off": []
        }
        
        success, response = self.run_test(
            "Create Worker",
            "POST",
            "workers",
            200,
            data=worker_data
        )
        if success and 'id' in response:
            self.created_worker_id = response['id']
            print(f"   Worker created with ID: {self.created_worker_id}")
            return True
        return False

    def test_get_workers(self):
        """Get all workers"""
        success, response = self.run_test(
            "Get Workers",
            "GET",
            "workers",
            200
        )
        if success:
            print(f"   Found {len(response)} workers")
            for worker in response:
                if worker.get('name') == 'Ana':
                    print(f"   ✅ Found created worker: {worker['name']} - {len(worker.get('services', []))} services")
        return success

    def test_available_slots(self):
        """Test getting available slots"""
        print("\n" + "="*50)
        print("TESTING BOOKING AVAILABILITY")
        print("="*50)
        
        if not self.created_service_id:
            print("❌ Cannot test slots - no service ID available")
            return False
            
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        slots_data = {
            "services": [self.created_service_id],
            "worker_id": self.created_worker_id,
            "date": tomorrow
        }
        
        success, response = self.run_test(
            "Get Available Slots",
            "POST",
            "reservations/available-slots",
            200,
            data=slots_data
        )
        if success:
            slots = response.get('slots', [])
            print(f"   Found {len(slots)} available slots for {tomorrow}")
            if slots:
                print(f"   First few slots: {slots[:5]}")
        return success

    def test_create_reservation(self):
        """Create a client reservation"""
        print("\n" + "="*50)
        print("TESTING RESERVATION CREATION")
        print("="*50)
        
        if not self.created_service_id:
            print("❌ Cannot create reservation - no service ID available")
            return False
            
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        reservation_data = {
            "services": [self.created_service_id],
            "worker_id": self.created_worker_id,
            "date": tomorrow,
            "time": "10:00",
            "client_name": "Marko Petrović",
            "client_phone": "+381601234567"
        }
        
        success, response = self.run_test(
            "Create Reservation",
            "POST",
            "reservations",
            200,
            data=reservation_data
        )
        if success and 'id' in response:
            self.created_reservation_id = response['id']
            print(f"   Reservation created with ID: {self.created_reservation_id}")
            print(f"   Client: {response.get('client_name')} - {response.get('client_phone')}")
            print(f"   Total: {response.get('total_price')} RSD")
            return True
        return False

    def test_get_reservations(self):
        """Get reservations for admin"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        success, response = self.run_test(
            "Get Reservations",
            "GET",
            f"reservations?date={tomorrow}",
            200
        )
        if success:
            print(f"   Found {len(response)} reservations for {tomorrow}")
            for res in response:
                print(f"   - {res.get('time')} {res.get('client_name')} ({res.get('total_price')} RSD)")
        return success

    def test_release_advance(self):
        """Test releasing advance payment"""
        print("\n" + "="*50)
        print("TESTING ADVANCE PAYMENT RELEASE")
        print("="*50)
        
        if not self.created_reservation_id:
            print("❌ Cannot release advance - no reservation ID available")
            return False
            
        success, response = self.run_test(
            "Release Advance Payment",
            "PUT",
            f"reservations/{self.created_reservation_id}/release-advance",
            200
        )
        if success:
            print("   ✅ Advance payment released successfully")
        return success

    def test_blacklist_phone(self):
        """Test blacklisting a phone number"""
        print("\n" + "="*50)
        print("TESTING PHONE BLACKLISTING")
        print("="*50)
        
        test_phone = "+381601234567"
        
        success, response = self.run_test(
            "Add Phone to Blacklist",
            "POST",
            f"blacklist?phone={test_phone}",
            200
        )
        if success:
            print(f"   ✅ Phone {test_phone} added to blacklist")
        return success

    def test_blacklisted_booking_attempt(self):
        """Test that blacklisted phone cannot create reservation"""
        if not self.created_service_id:
            print("❌ Cannot test blacklisted booking - no service ID available")
            return False
            
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        reservation_data = {
            "services": [self.created_service_id],
            "worker_id": self.created_worker_id,
            "date": tomorrow,
            "time": "11:00",
            "client_name": "Blocked User",
            "client_phone": "+381601234567"  # Same phone that was blacklisted
        }
        
        success, response = self.run_test(
            "Blacklisted Phone Booking Attempt",
            "POST",
            "reservations",
            403,  # Should be forbidden
            data=reservation_data
        )
        if success:
            print("   ✅ Blacklisted phone correctly blocked from booking")
        return success

    def test_max_reservations_limit(self):
        """Test max 3 reservations per phone per day limit"""
        print("\n" + "="*50)
        print("TESTING RESERVATION LIMITS")
        print("="*50)
        
        if not self.created_service_id:
            print("❌ Cannot test reservation limits - no service ID available")
            return False
            
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        test_phone = "+381609999999"
        
        # Try to create 4 reservations with the same phone
        times = ["12:00", "13:00", "14:00", "15:00"]
        successful_bookings = 0
        
        for i, time in enumerate(times):
            reservation_data = {
                "services": [self.created_service_id],
                "worker_id": self.created_worker_id,
                "date": tomorrow,
                "time": time,
                "client_name": f"Test User {i+1}",
                "client_phone": test_phone
            }
            
            expected_status = 200 if i < 3 else 400  # First 3 should succeed, 4th should fail
            success, response = self.run_test(
                f"Reservation {i+1}/4 for same phone",
                "POST",
                "reservations",
                expected_status,
                data=reservation_data
            )
            
            if success and expected_status == 200:
                successful_bookings += 1
            elif success and expected_status == 400:
                print(f"   ✅ 4th reservation correctly rejected (limit reached)")
                return True
                
        print(f"   Created {successful_bookings} reservations before limit")
        return successful_bookings == 3

    def test_settings(self):
        """Test settings endpoints"""
        print("\n" + "="*50)
        print("TESTING SETTINGS")
        print("="*50)
        
        # Get settings
        success, response = self.run_test(
            "Get Settings",
            "GET",
            "settings",
            200
        )
        if success:
            print(f"   Salon: {response.get('salon_name')}")
            print(f"   Hours: {response.get('work_start')} - {response.get('work_end')}")
        
        return success

def main():
    print("🏪 SALON BOOKING API TESTING")
    print("="*60)
    
    tester = SalonAPITester()
    
    # Test sequence
    tests = [
        ("Admin Authentication", [
            tester.test_admin_login,
            tester.test_get_me,
        ]),
        ("Service Management", [
            tester.test_create_service,
            tester.test_get_services,
        ]),
        ("Worker Management", [
            tester.test_create_worker,
            tester.test_get_workers,
        ]),
        ("Booking System", [
            tester.test_available_slots,
            tester.test_create_reservation,
            tester.test_get_reservations,
        ]),
        ("Advanced Features", [
            tester.test_release_advance,
            tester.test_blacklist_phone,
            tester.test_blacklisted_booking_attempt,
            tester.test_max_reservations_limit,
        ]),
        ("Settings", [
            tester.test_settings,
        ]),
    ]
    
    # Run all tests
    for category, test_functions in tests:
        print(f"\n{'='*20} {category} {'='*20}")
        for test_func in test_functions:
            if not test_func():
                print(f"❌ Critical test failed in {category}, continuing...")
    
    # Print final results
    print("\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())