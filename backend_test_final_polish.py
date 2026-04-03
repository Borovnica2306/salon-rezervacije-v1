#!/usr/bin/env python3

import requests
import sys
from datetime import datetime, timedelta
import json

class BeautyStudioAPITester:
    def __init__(self, base_url="https://slot-reserve-23.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)

            print(f"   Status: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error text: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login and get token"""
        print("\n=== Testing Admin Authentication ===")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@salon.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Admin login successful, token obtained")
            return True
        return False

    def test_basic_endpoints(self):
        """Test basic data endpoints"""
        print("\n=== Testing Basic Data Endpoints ===")
        
        # Test services
        success, services = self.run_test("Get Services", "GET", "services", 200)
        if success:
            print(f"   Found {len(services)} services")
        
        # Test workers
        success, workers = self.run_test("Get Workers", "GET", "workers", 200)
        if success:
            print(f"   Found {len(workers)} workers")
        
        # Test settings
        success, settings = self.run_test("Get Settings", "GET", "settings", 200)
        if success:
            print(f"   Settings loaded")

    def test_availability(self):
        """Test availability endpoint"""
        print("\n=== Testing Availability ===")
        
        # First get services to use in availability check
        success, services = self.run_test("Get Services for Availability", "GET", "services", 200)
        if not success or not services:
            print("❌ Cannot test availability - no services found")
            return
        
        # Use first service for availability check
        service_id = services[0]['id']
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Test availability for today
        success, availability = self.run_test(
            "Check Availability Today",
            "POST",
            "reservations/available-slots",
            200,
            data={
                "services": [service_id],
                "worker_id": None,
                "date": today
            }
        )
        
        if success:
            slots = availability.get('slots', [])
            print(f"   Available slots today: {len(slots)}")
            if len(slots) == 0:
                print("   ⚠️ No slots available today")
        
        # Test availability for tomorrow
        success, availability = self.run_test(
            "Check Availability Tomorrow",
            "POST",
            "reservations/available-slots",
            200,
            data={
                "services": [service_id],
                "worker_id": None,
                "date": tomorrow
            }
        )
        
        if success:
            slots = availability.get('slots', [])
            print(f"   Available slots tomorrow: {len(slots)}")
            if len(slots) == 0:
                print("   ⚠️ No slots available tomorrow")

    def test_my_reservations(self):
        """Test my reservations endpoint"""
        print("\n=== Testing My Reservations ===")
        
        success, reservations = self.run_test(
            "Search My Reservations",
            "POST",
            "my-reservations",
            200,
            data={"phone": "+381 60 123 4567"}
        )
        
        if success:
            print(f"   Found {len(reservations)} reservations for test phone")

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        if not self.token:
            print("❌ Cannot test admin endpoints - no token")
            return
            
        print("\n=== Testing Admin Endpoints ===")
        
        # Test get all reservations
        success, reservations = self.run_test(
            "Get All Reservations (Admin)",
            "GET",
            "reservations",
            200
        )
        
        if success:
            print(f"   Found {len(reservations)} total reservations")

def main():
    print("🧪 Beauty Studio Bor - Final Polish API Testing")
    print("=" * 50)
    
    tester = BeautyStudioAPITester()
    
    # Test basic endpoints first
    tester.test_basic_endpoints()
    
    # Test availability (this is key for booking flow)
    tester.test_availability()
    
    # Test my reservations
    tester.test_my_reservations()
    
    # Test admin login
    if tester.test_admin_login():
        tester.test_admin_endpoints()
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())