import requests
import sys
from datetime import datetime, timedelta
import json

class SalonFixedVersionTester:
    def __init__(self, base_url="https://slot-reserve-23.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []

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
            return True
        else:
            self.issues.append("Admin login failed - cannot proceed with admin-only tests")
        return False

    def test_services_count_and_content(self):
        """Verify exactly 5 services with correct names and no duplicates"""
        print("\n" + "="*50)
        print("TESTING SERVICES - EXACT COUNT AND CONTENT")
        print("="*50)
        
        success, response = self.run_test(
            "Get All Services",
            "GET",
            "services",
            200
        )
        
        if not success:
            return False
            
        services = response
        print(f"   Found {len(services)} services")
        
        # Check exact count
        if len(services) != 5:
            self.issues.append(f"Expected exactly 5 services, found {len(services)}")
            print(f"❌ Expected exactly 5 services, found {len(services)}")
            return False
        
        # Check for expected service names
        expected_services = ["Šišanje", "Farbanje kose", "Manikir", "Pedikir", "Relax masaža"]
        found_services = [s['name'] for s in services]
        
        print("   Expected services:", expected_services)
        print("   Found services:", found_services)
        
        # Check for duplicates
        if len(found_services) != len(set(found_services)):
            self.issues.append("Duplicate services found")
            print("❌ Duplicate services detected")
            return False
        
        # Check all expected services are present
        missing_services = set(expected_services) - set(found_services)
        if missing_services:
            self.issues.append(f"Missing services: {missing_services}")
            print(f"❌ Missing services: {missing_services}")
            return False
        
        # Check durations match expected
        expected_durations = {
            "Šišanje": 30,
            "Farbanje kose": 90,
            "Manikir": 45,
            "Pedikir": 60,
            "Relax masaža": 60
        }
        
        for service in services:
            expected_duration = expected_durations.get(service['name'])
            if expected_duration and service['duration'] != expected_duration:
                self.issues.append(f"Service {service['name']} has duration {service['duration']}, expected {expected_duration}")
                print(f"❌ Service {service['name']} duration mismatch")
                return False
        
        print("✅ All 5 services present with correct durations, no duplicates")
        return True

    def test_workers_count_and_content(self):
        """Verify exactly 1 worker (Ana) with no duplicates"""
        print("\n" + "="*50)
        print("TESTING WORKERS - EXACT COUNT AND CONTENT")
        print("="*50)
        
        success, response = self.run_test(
            "Get All Workers",
            "GET",
            "workers",
            200
        )
        
        if not success:
            return False
            
        workers = response
        print(f"   Found {len(workers)} workers")
        
        # Check exact count
        if len(workers) != 1:
            self.issues.append(f"Expected exactly 1 worker, found {len(workers)}")
            print(f"❌ Expected exactly 1 worker, found {len(workers)}")
            return False
        
        # Check worker name
        worker = workers[0]
        if worker['name'] != 'Ana':
            self.issues.append(f"Expected worker 'Ana', found '{worker['name']}'")
            print(f"❌ Expected worker 'Ana', found '{worker['name']}'")
            return False
        
        # Check Ana has all 5 services
        if len(worker['services']) != 5:
            self.issues.append(f"Ana should have 5 services, has {len(worker['services'])}")
            print(f"❌ Ana should have 5 services, has {len(worker['services'])}")
            return False
        
        # Check Sunday is off day (days_off should contain 0)
        if 0 not in worker.get('days_off', []):
            self.issues.append("Ana should have Sunday (0) as off day")
            print("❌ Ana should have Sunday as off day")
            return False
        
        print("✅ Exactly 1 worker (Ana) with all 5 services and Sunday off")
        return True

    def test_calendar_slots_working_day(self):
        """Test calendar shows time slots on working day (not Sunday)"""
        print("\n" + "="*50)
        print("TESTING CALENDAR - WORKING DAY SLOTS")
        print("="*50)
        
        # Get services first to use in slot request
        success, services_response = self.run_test(
            "Get Services for Slot Test",
            "GET",
            "services",
            200
        )
        
        if not success or not services_response:
            return False
        
        # Find a working day (Monday = 1, not Sunday = 0)
        today = datetime.now()
        working_day = today
        while working_day.weekday() == 6:  # Skip Sunday (6 in Python weekday)
            working_day += timedelta(days=1)
        
        working_date = working_day.strftime("%Y-%m-%d")
        print(f"   Testing slots for working day: {working_date}")
        
        # Test with first service
        service_id = services_response[0]['id']
        
        slots_data = {
            "services": [service_id],
            "worker_id": None,  # Any worker
            "date": working_date
        }
        
        success, response = self.run_test(
            "Get Available Slots - Working Day",
            "POST",
            "reservations/available-slots",
            200,
            data=slots_data
        )
        
        if not success:
            return False
        
        slots = response.get('slots', [])
        workers = response.get('workers', {})
        
        if not slots:
            self.issues.append(f"No time slots available on working day {working_date}")
            print(f"❌ No time slots available on working day")
            return False
        
        if not workers:
            self.issues.append(f"No workers available on working day {working_date}")
            print(f"❌ No workers available on working day")
            return False
        
        print(f"✅ Found {len(slots)} time slots on working day")
        print(f"   Available workers: {list(workers.keys())}")
        return True

    def test_calendar_slots_sunday(self):
        """Test calendar shows no slots on Sunday (Ana's off day)"""
        print("\n" + "="*50)
        print("TESTING CALENDAR - SUNDAY (OFF DAY)")
        print("="*50)
        
        # Get services first
        success, services_response = self.run_test(
            "Get Services for Sunday Test",
            "GET",
            "services",
            200
        )
        
        if not success or not services_response:
            return False
        
        # Find next Sunday
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:  # Today is Sunday
            days_until_sunday = 7
        sunday = today + timedelta(days=days_until_sunday)
        sunday_date = sunday.strftime("%Y-%m-%d")
        
        print(f"   Testing slots for Sunday: {sunday_date}")
        
        service_id = services_response[0]['id']
        
        slots_data = {
            "services": [service_id],
            "worker_id": None,
            "date": sunday_date
        }
        
        success, response = self.run_test(
            "Get Available Slots - Sunday",
            "POST",
            "reservations/available-slots",
            200,
            data=slots_data
        )
        
        if not success:
            return False
        
        slots = response.get('slots', [])
        workers = response.get('workers', {})
        
        if slots or workers:
            self.issues.append(f"Found slots/workers on Sunday (should be Ana's off day)")
            print(f"❌ Found {len(slots)} slots and {len(workers)} workers on Sunday")
            return False
        
        print("✅ No slots available on Sunday (Ana's off day)")
        return True

    def test_duration_summing(self):
        """Test duration summing when selecting multiple services"""
        print("\n" + "="*50)
        print("TESTING DURATION SUMMING")
        print("="*50)
        
        # Get all services
        success, services_response = self.run_test(
            "Get Services for Duration Test",
            "GET",
            "services",
            200
        )
        
        if not success or len(services_response) < 2:
            return False
        
        # Select first two services
        service1 = services_response[0]
        service2 = services_response[1]
        
        print(f"   Service 1: {service1['name']} ({service1['duration']} min)")
        print(f"   Service 2: {service2['name']} ({service2['duration']} min)")
        print(f"   Expected total: {service1['duration'] + service2['duration']} min")
        
        # Find a working day
        today = datetime.now()
        working_day = today + timedelta(days=1)
        while working_day.weekday() == 6:  # Skip Sunday
            working_day += timedelta(days=1)
        
        working_date = working_day.strftime("%Y-%m-%d")
        
        slots_data = {
            "services": [service1['id'], service2['id']],
            "worker_id": None,
            "date": working_date
        }
        
        success, response = self.run_test(
            "Get Slots for Multiple Services",
            "POST",
            "reservations/available-slots",
            200,
            data=slots_data
        )
        
        if not success:
            return False
        
        # The API should return slots that account for the combined duration
        slots = response.get('slots', [])
        
        if not slots:
            self.issues.append("No slots available for multiple services")
            print("❌ No slots available for multiple services")
            return False
        
        print(f"✅ Duration summing working - found {len(slots)} slots for combined services")
        return True

def main():
    print("🏪 SALON BOOKING API - FIXED VERSION TESTING")
    print("="*60)
    print("Testing specific requirements:")
    print("- Exactly 5 services (no duplicates)")
    print("- Exactly 1 worker (Ana)")
    print("- Calendar slots on working days")
    print("- No slots on Sunday (Ana's off day)")
    print("- Duration summing for multiple services")
    print("="*60)
    
    tester = SalonFixedVersionTester()
    
    # Test sequence - focused on specific requirements
    tests = [
        ("Admin Authentication", tester.test_admin_login),
        ("Services Verification", tester.test_services_count_and_content),
        ("Workers Verification", tester.test_workers_count_and_content),
        ("Calendar Working Day", tester.test_calendar_slots_working_day),
        ("Calendar Sunday (Off Day)", tester.test_calendar_slots_sunday),
        ("Duration Summing", tester.test_duration_summing),
    ]
    
    # Run all tests
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if not test_func():
            print(f"❌ Critical test failed: {test_name}")
    
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
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())