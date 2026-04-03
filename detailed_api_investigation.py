#!/usr/bin/env python3

import requests
import sys
from datetime import datetime, timedelta
import json

class DetailedAPITester:
    def __init__(self, base_url="https://slot-reserve-23.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None

    def get_admin_token(self):
        """Get admin token"""
        try:
            response = requests.post(f"{self.api_url}/auth/login", 
                json={"email": "admin@salon.com", "password": "Admin123!"}, 
                timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                print(f"✅ Admin token obtained")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_workers_discrepancy(self):
        """Test the workers API discrepancy"""
        print("\n=== Investigating Workers API Discrepancy ===")
        
        # Test public workers endpoint
        try:
            response = requests.get(f"{self.api_url}/workers", timeout=10)
            print(f"Public workers endpoint status: {response.status_code}")
            if response.status_code == 200:
                workers = response.json()
                print(f"Public workers count: {len(workers)}")
                if workers:
                    for worker in workers:
                        print(f"  - Worker: {worker}")
            else:
                print(f"Public workers error: {response.text}")
        except Exception as e:
            print(f"Public workers error: {e}")
        
        # Test admin workers endpoint if token available
        if self.token:
            try:
                headers = {'Authorization': f'Bearer {self.token}'}
                response = requests.get(f"{self.api_url}/workers", headers=headers, timeout=10)
                print(f"Admin workers endpoint status: {response.status_code}")
                if response.status_code == 200:
                    workers = response.json()
                    print(f"Admin workers count: {len(workers)}")
                    if workers:
                        for worker in workers:
                            print(f"  - Admin Worker: {worker}")
                else:
                    print(f"Admin workers error: {response.text}")
            except Exception as e:
                print(f"Admin workers error: {e}")
        
        # Try alternative endpoints
        alternative_endpoints = [
            "/admin/workers",
            "/workers/all", 
            "/staff",
            "/employees"
        ]
        
        for endpoint in alternative_endpoints:
            try:
                headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
                response = requests.get(f"{self.api_url}{endpoint}", headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Found workers at {endpoint}: {len(data) if isinstance(data, list) else 'object'}")
                    if isinstance(data, list) and data:
                        print(f"  First worker: {data[0]}")
            except:
                pass

    def test_availability_with_specific_worker(self):
        """Test availability with specific worker ID"""
        print("\n=== Testing Availability with Worker ID ===")
        
        # Get services first
        try:
            response = requests.get(f"{self.api_url}/services", timeout=10)
            if response.status_code == 200:
                services = response.json()
                if services:
                    service_id = services[0]['id']
                    print(f"Using service ID: {service_id}")
                    
                    # Test with different worker IDs
                    worker_ids_to_test = [None, 1, "1", "ana", "Ana"]
                    
                    for worker_id in worker_ids_to_test:
                        try:
                            data = {
                                "services": [service_id],
                                "worker_id": worker_id,
                                "date": datetime.now().strftime("%Y-%m-%d")
                            }
                            response = requests.post(f"{self.api_url}/reservations/available-slots", 
                                json=data, timeout=10)
                            
                            print(f"Worker ID {worker_id}: Status {response.status_code}")
                            if response.status_code == 200:
                                result = response.json()
                                slots = result.get('slots', [])
                                workers = result.get('workers', {})
                                print(f"  Slots: {len(slots)}, Workers: {workers}")
                            else:
                                print(f"  Error: {response.text[:100]}")
                        except Exception as e:
                            print(f"  Error with worker {worker_id}: {e}")
        except Exception as e:
            print(f"Error getting services: {e}")

    def test_database_direct_queries(self):
        """Test if there are any direct database query endpoints"""
        print("\n=== Testing Database Query Endpoints ===")
        
        if not self.token:
            print("No admin token available")
            return
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Try various admin endpoints that might show raw data
        test_endpoints = [
            "/admin/data",
            "/admin/debug",
            "/admin/stats",
            "/debug/workers",
            "/debug/data",
            "/system/info"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"{self.api_url}{endpoint}", headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint}: {type(data)} - {str(data)[:100]}")
            except:
                pass

def main():
    print("🔍 Detailed API Investigation - Workers Discrepancy")
    print("=" * 60)
    
    tester = DetailedAPITester()
    
    # Get admin token
    if tester.get_admin_token():
        tester.test_workers_discrepancy()
        tester.test_availability_with_specific_worker()
        tester.test_database_direct_queries()
    else:
        print("Cannot proceed without admin token")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())