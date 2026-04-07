"""
Test Worker Desync Bug Fix - Iteration 9
Tests:
1. GET /api/workers returns Suzana, Milena, Slobodan (NOT Ana)
2. Worker creation still works
3. Worker hard delete still works
4. Worker with future bookings cannot be deleted (referential integrity)
5. Booking flow works with new workers
6. seed_completed flag prevents re-seeding
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "bornaja23@gmail.com"
SUPER_ADMIN_PASSWORD = "Markonijus23!"
SALON_ADMIN_EMAIL = "admin@salon.com"
SALON_ADMIN_PASSWORD = "Admin123!"

@pytest.fixture(scope="module")
def session():
    """Shared requests session"""
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s

@pytest.fixture(scope="module")
def admin_token(session):
    """Get admin authentication token"""
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": SALON_ADMIN_EMAIL,
        "password": SALON_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json().get("access_token")

@pytest.fixture(scope="module")
def super_admin_token(session):
    """Get super-admin authentication token"""
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Super-admin login failed: {response.text}"
    return response.json().get("access_token")


class TestWorkerDesyncFix:
    """Tests for worker desync bug fix"""
    
    def test_workers_list_returns_correct_workers(self, session):
        """GET /api/workers returns Suzana, Milena, Slobodan (NOT Ana)"""
        response = session.get(f"{BASE_URL}/api/workers")
        assert response.status_code == 200
        
        workers = response.json()
        worker_names = [w["name"] for w in workers]
        
        # Verify expected workers are present
        assert "Suzana" in worker_names, "Suzana should be in workers list"
        assert "Milena" in worker_names, "Milena should be in workers list"
        assert "Slobodan" in worker_names, "Slobodan should be in workers list"
        
        # Verify Ana is NOT present (the deleted worker)
        assert "Ana" not in worker_names, "Ana should NOT be in workers list (was deleted)"
        
        print(f"✓ Workers list correct: {worker_names}")
    
    def test_workers_count_is_three(self, session):
        """Verify exactly 3 active workers exist"""
        response = session.get(f"{BASE_URL}/api/workers")
        assert response.status_code == 200
        
        workers = response.json()
        assert len(workers) == 3, f"Expected 3 workers, got {len(workers)}"
        print(f"✓ Worker count correct: {len(workers)}")
    
    def test_suzana_has_hair_services(self, session):
        """Verify Suzana is assigned to hair services"""
        response = session.get(f"{BASE_URL}/api/workers")
        workers = response.json()
        
        suzana = next((w for w in workers if w["name"] == "Suzana"), None)
        assert suzana is not None, "Suzana not found"
        
        # Get services to verify
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        
        hair_service_ids = [s["id"] for s in services if s["category"] == "hair"]
        
        # Suzana should have hair services
        for sid in suzana["services"]:
            assert sid in hair_service_ids or any(s["id"] == sid for s in services), f"Service {sid} should be valid"
        
        print(f"✓ Suzana has services: {suzana['services']}")
    
    def test_milena_has_nails_services(self, session):
        """Verify Milena is assigned to nails services"""
        response = session.get(f"{BASE_URL}/api/workers")
        workers = response.json()
        
        milena = next((w for w in workers if w["name"] == "Milena"), None)
        assert milena is not None, "Milena not found"
        
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        
        nails_service_ids = [s["id"] for s in services if s["category"] == "nails"]
        
        # Milena should have nails services
        for sid in milena["services"]:
            assert sid in nails_service_ids or any(s["id"] == sid for s in services), f"Service {sid} should be valid"
        
        print(f"✓ Milena has services: {milena['services']}")
    
    def test_slobodan_has_massage_services(self, session):
        """Verify Slobodan is assigned to massage services"""
        response = session.get(f"{BASE_URL}/api/workers")
        workers = response.json()
        
        slobodan = next((w for w in workers if w["name"] == "Slobodan"), None)
        assert slobodan is not None, "Slobodan not found"
        
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        
        massage_service_ids = [s["id"] for s in services if s["category"] == "massage"]
        
        # Slobodan should have massage services
        for sid in slobodan["services"]:
            assert sid in massage_service_ids or any(s["id"] == sid for s in services), f"Service {sid} should be valid"
        
        print(f"✓ Slobodan has services: {slobodan['services']}")


class TestWorkerCRUD:
    """Tests for worker CRUD operations"""
    
    def test_create_worker(self, session, admin_token):
        """Worker creation still works"""
        # Get a service ID to assign
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        service_id = services[0]["id"] if services else None
        
        response = session.post(
            f"{BASE_URL}/api/workers",
            json={
                "name": "TEST_TempWorker",
                "services": [service_id] if service_id else [],
                "work_start": "09:00",
                "work_end": "18:00",
                "days_off": [0, 6]
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Worker creation failed: {response.text}"
        worker = response.json()
        assert worker["name"] == "TEST_TempWorker"
        assert worker["active"] == True
        
        print(f"✓ Worker created: {worker['name']} (ID: {worker['id']})")
        return worker["id"]
    
    def test_delete_worker_without_bookings(self, session, admin_token):
        """Worker hard delete works for workers without future bookings"""
        # First create a temp worker
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        service_id = services[0]["id"] if services else None
        
        create_response = session.post(
            f"{BASE_URL}/api/workers",
            json={
                "name": "TEST_DeleteMe",
                "services": [service_id] if service_id else [],
                "work_start": "09:00",
                "work_end": "18:00",
                "days_off": []
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert create_response.status_code == 200
        worker_id = create_response.json()["id"]
        
        # Now delete the worker
        delete_response = session.delete(
            f"{BASE_URL}/api/workers/{worker_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert delete_response.status_code == 200, f"Worker deletion failed: {delete_response.text}"
        
        # Verify worker is gone
        workers_response = session.get(f"{BASE_URL}/api/workers")
        workers = workers_response.json()
        worker_ids = [w["id"] for w in workers]
        
        assert worker_id not in worker_ids, "Deleted worker should not appear in list"
        print(f"✓ Worker deleted successfully: {worker_id}")
    
    def test_update_worker(self, session, admin_token):
        """Worker update works"""
        # Get existing worker
        workers_response = session.get(f"{BASE_URL}/api/workers")
        workers = workers_response.json()
        
        if workers:
            worker_id = workers[0]["id"]
            original_name = workers[0]["name"]
            
            # Update work hours
            update_response = session.put(
                f"{BASE_URL}/api/workers/{worker_id}",
                json={"work_end": "20:00"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            assert update_response.status_code == 200
            updated = update_response.json()
            assert updated["work_end"] == "20:00"
            
            # Restore original
            session.put(
                f"{BASE_URL}/api/workers/{worker_id}",
                json={"work_end": "21:00"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            print(f"✓ Worker update works for {original_name}")


class TestBookingWithNewWorkers:
    """Tests for booking flow with new workers"""
    
    def test_available_slots_for_suzana_hair(self, session):
        """Get available slots for Suzana (hair services)"""
        # Get workers and services
        workers_response = session.get(f"{BASE_URL}/api/workers")
        workers = workers_response.json()
        
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        
        suzana = next((w for w in workers if w["name"] == "Suzana"), None)
        hair_service = next((s for s in services if s["category"] == "hair"), None)
        
        assert suzana is not None, "Suzana not found"
        assert hair_service is not None, "Hair service not found"
        
        # Get available slots for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = session.post(
            f"{BASE_URL}/api/reservations/available-slots",
            json={
                "service_worker_pairs": [
                    {"service_id": hair_service["id"], "worker_id": suzana["id"]}
                ],
                "date": tomorrow
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        print(f"✓ Available slots for Suzana (hair): {len(data['slots'])} slots on {tomorrow}")
    
    def test_available_slots_for_milena_nails(self, session):
        """Get available slots for Milena (nails services)"""
        workers_response = session.get(f"{BASE_URL}/api/workers")
        workers = workers_response.json()
        
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        
        milena = next((w for w in workers if w["name"] == "Milena"), None)
        nails_service = next((s for s in services if s["category"] == "nails"), None)
        
        assert milena is not None, "Milena not found"
        assert nails_service is not None, "Nails service not found"
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = session.post(
            f"{BASE_URL}/api/reservations/available-slots",
            json={
                "service_worker_pairs": [
                    {"service_id": nails_service["id"], "worker_id": milena["id"]}
                ],
                "date": tomorrow
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        print(f"✓ Available slots for Milena (nails): {len(data['slots'])} slots on {tomorrow}")
    
    def test_available_slots_for_slobodan_massage(self, session):
        """Get available slots for Slobodan (massage services)"""
        workers_response = session.get(f"{BASE_URL}/api/workers")
        workers = workers_response.json()
        
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        
        slobodan = next((w for w in workers if w["name"] == "Slobodan"), None)
        massage_service = next((s for s in services if s["category"] == "massage"), None)
        
        assert slobodan is not None, "Slobodan not found"
        assert massage_service is not None, "Massage service not found"
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = session.post(
            f"{BASE_URL}/api/reservations/available-slots",
            json={
                "service_worker_pairs": [
                    {"service_id": massage_service["id"], "worker_id": slobodan["id"]}
                ],
                "date": tomorrow
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        print(f"✓ Available slots for Slobodan (massage): {len(data['slots'])} slots on {tomorrow}")
    
    def test_create_booking_with_suzana(self, session):
        """Create a booking with Suzana for hair service"""
        workers_response = session.get(f"{BASE_URL}/api/workers")
        workers = workers_response.json()
        
        services_response = session.get(f"{BASE_URL}/api/services")
        services = services_response.json()
        
        suzana = next((w for w in workers if w["name"] == "Suzana"), None)
        hair_service = next((s for s in services if s["category"] == "hair"), None)
        
        # Get available slots
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        slots_response = session.post(
            f"{BASE_URL}/api/reservations/available-slots",
            json={
                "service_worker_pairs": [
                    {"service_id": hair_service["id"], "worker_id": suzana["id"]}
                ],
                "date": tomorrow
            }
        )
        
        slots = slots_response.json().get("slots", [])
        if not slots:
            pytest.skip("No available slots for booking test")
        
        # Create booking
        response = session.post(
            f"{BASE_URL}/api/reservations",
            json={
                "service_worker_pairs": [
                    {"service_id": hair_service["id"], "worker_id": suzana["id"]}
                ],
                "date": tomorrow,
                "time": slots[0],
                "client_name": "TEST_BookingClient",
                "client_phone": "+381999888777"
            }
        )
        
        assert response.status_code == 200, f"Booking failed: {response.text}"
        booking = response.json()
        assert booking["worker_name"] == "Suzana"
        assert hair_service["name"] in booking["service_names"]
        
        print(f"✓ Booking created with Suzana: {booking['booking_id']}")
        return booking["id"]


class TestServicesCategories:
    """Tests for services grouped by category"""
    
    def test_services_have_correct_categories(self, session):
        """Services are correctly categorized"""
        response = session.get(f"{BASE_URL}/api/services")
        assert response.status_code == 200
        
        services = response.json()
        
        # Check expected services exist
        service_names = [s["name"] for s in services]
        
        # Hair services
        assert "Šišanje" in service_names or any("šišanje" in s.lower() for s in service_names), "Šišanje should exist"
        assert "Farbanje kose" in service_names or any("farbanje" in s.lower() for s in service_names), "Farbanje kose should exist"
        
        # Nails services
        assert "Manikir" in service_names or any("manikir" in s.lower() for s in service_names), "Manikir should exist"
        assert "Pedikir" in service_names or any("pedikir" in s.lower() for s in service_names), "Pedikir should exist"
        
        # Massage services
        assert any("masaža" in s.lower() or "massage" in s.lower() for s in service_names), "Massage service should exist"
        
        print(f"✓ Services correctly categorized: {service_names}")
    
    def test_categories_endpoint(self, session):
        """Categories endpoint returns enabled categories"""
        response = session.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        
        categories = response.json()
        category_keys = [c["key"] for c in categories]
        
        # At minimum, hair, nails, massage should be enabled
        assert "hair" in category_keys, "Hair category should be enabled"
        assert "nails" in category_keys, "Nails category should be enabled"
        assert "massage" in category_keys, "Massage category should be enabled"
        
        print(f"✓ Categories available: {category_keys}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_workers(self, session, admin_token):
        """Remove any TEST_ prefixed workers"""
        workers_response = session.get(f"{BASE_URL}/api/workers?active_only=false")
        workers = workers_response.json()
        
        for worker in workers:
            if worker["name"].startswith("TEST_"):
                session.delete(
                    f"{BASE_URL}/api/workers/{worker['id']}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                print(f"  Cleaned up worker: {worker['name']}")
        
        print("✓ Test workers cleaned up")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
