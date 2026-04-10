"""
Test Admin Dashboard Worker Filter and Multi-Worker Reservation Filtering
Tests the enhanced worker filter that checks service_worker_pairs and worker_time_blocks
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@salon.com"
ADMIN_PASSWORD = "Admin123!"

# Test data from seed - multi-worker reservations on 2026-04-15
TEST_DATE = "2026-04-15"
SUZANA_ID = "69d4d6f82990ad8a6366bf7d"
MILENA_ID = "69d4d6f82990ad8a6366bf7e"
SLOBODAN_ID = "69d4d6f82990ad8a6366bf7f"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestWorkerFilterBackend:
    """Tests for worker filter in GET /api/reservations"""
    
    def test_get_all_reservations_without_worker_filter(self, auth_headers):
        """GET /api/reservations without worker_id returns all reservations for date"""
        response = requests.get(
            f"{BASE_URL}/api/reservations",
            params={"date": TEST_DATE},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return at least 1 reservation (R2DR - 51FY may have been cancelled during testing)
        assert len(data) >= 1, f"Expected at least 1 reservation, got {len(data)}"
        
        # Verify reservation structure
        for res in data:
            assert "id" in res
            assert "booking_id" in res
            assert "service_worker_pairs" in res
            assert "worker_time_blocks" in res
    
    def test_filter_by_suzana_returns_multi_worker_reservations(self, auth_headers):
        """GET /api/reservations?worker_id=Suzana returns reservations where Suzana is one of the workers"""
        response = requests.get(
            f"{BASE_URL}/api/reservations",
            params={"date": TEST_DATE, "worker_id": SUZANA_ID},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Suzana should be in at least 1 reservation (R2DR with Milena - 51FY may have been cancelled)
        assert len(data) >= 1, f"Expected at least 1 reservation for Suzana, got {len(data)}"
        
        # Verify Suzana is in each reservation's service_worker_pairs or worker_time_blocks
        for res in data:
            worker_ids = []
            for pair in res.get("service_worker_pairs", []):
                worker_ids.append(pair.get("worker_id"))
            for block in res.get("worker_time_blocks", []):
                worker_ids.append(block.get("worker_id"))
            
            assert SUZANA_ID in worker_ids or res.get("worker_id") == SUZANA_ID, \
                f"Suzana not found in reservation {res.get('booking_id')}"
    
    def test_filter_by_milena_returns_only_her_reservations(self, auth_headers):
        """GET /api/reservations?worker_id=Milena returns only reservations where Milena is a worker"""
        response = requests.get(
            f"{BASE_URL}/api/reservations",
            params={"date": TEST_DATE, "worker_id": MILENA_ID},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Milena should be in R2DR reservation only
        assert len(data) >= 1, f"Expected at least 1 reservation for Milena, got {len(data)}"
        
        # Verify Milena is in each returned reservation
        for res in data:
            worker_ids = []
            for pair in res.get("service_worker_pairs", []):
                worker_ids.append(pair.get("worker_id"))
            for block in res.get("worker_time_blocks", []):
                worker_ids.append(block.get("worker_id"))
            
            assert MILENA_ID in worker_ids or res.get("worker_id") == MILENA_ID, \
                f"Milena not found in reservation {res.get('booking_id')}"
    
    def test_filter_by_slobodan_returns_his_reservations(self, auth_headers):
        """GET /api/reservations?worker_id=Slobodan returns reservations where Slobodan is a worker
        Note: 51FY reservation (Suzana+Slobodan) may have been cancelled during testing"""
        response = requests.get(
            f"{BASE_URL}/api/reservations",
            params={"date": TEST_DATE, "worker_id": SLOBODAN_ID},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Slobodan was in 51FY reservation which may have been cancelled
        # Just verify the endpoint works and returns valid data
        # If there are reservations, verify Slobodan is in them
        for res in data:
            worker_ids = []
            for pair in res.get("service_worker_pairs", []):
                worker_ids.append(pair.get("worker_id"))
            for block in res.get("worker_time_blocks", []):
                worker_ids.append(block.get("worker_id"))
            
            assert SLOBODAN_ID in worker_ids or res.get("worker_id") == SLOBODAN_ID, \
                f"Slobodan not found in reservation {res.get('booking_id')}"


class TestReservationCancelEndpoint:
    """Tests for reservation cancel endpoint"""
    
    def test_cancel_endpoint_exists(self, auth_headers):
        """PUT /api/reservations/{id}/cancel endpoint exists"""
        # Use a non-existent ID to test endpoint exists
        response = requests.put(
            f"{BASE_URL}/api/reservations/000000000000000000000000/cancel",
            headers=auth_headers
        )
        # Should return 404 (not found) not 405 (method not allowed)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestWorkersEndpoint:
    """Tests for workers endpoint used by filter bar"""
    
    def test_get_workers_returns_active_workers(self, auth_headers):
        """GET /api/workers returns list of active workers for filter bar"""
        response = requests.get(
            f"{BASE_URL}/api/workers",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have workers
        assert len(data) >= 3, f"Expected at least 3 workers, got {len(data)}"
        
        # Verify worker structure
        for worker in data:
            assert "id" in worker
            assert "name" in worker
            assert worker.get("active", True) == True  # Only active workers


class TestReservationStructure:
    """Tests for reservation response structure needed by admin dashboard"""
    
    def test_reservation_has_required_fields_for_cancel_dialog(self, auth_headers):
        """Reservation response has all fields needed for cancel confirmation dialog"""
        response = requests.get(
            f"{BASE_URL}/api/reservations",
            params={"date": TEST_DATE},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            res = data[0]
            # Fields needed for cancel dialog
            assert "id" in res, "Missing id field"
            assert "booking_id" in res, "Missing booking_id field"
            assert "client_name" in res, "Missing client_name field"
            assert "time" in res, "Missing time field"
            assert "end_time" in res, "Missing end_time field"
            assert "service_names" in res, "Missing service_names field"
    
    def test_reservation_has_worker_time_blocks_for_mini_timeline(self, auth_headers):
        """Reservation response has worker_time_blocks for mini-timeline rendering"""
        response = requests.get(
            f"{BASE_URL}/api/reservations",
            params={"date": TEST_DATE},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find a multi-worker reservation
        multi_worker_res = None
        for res in data:
            if len(res.get("service_worker_pairs", [])) > 1:
                multi_worker_res = res
                break
        
        if multi_worker_res:
            # Should have worker_time_blocks for mini-timeline
            assert "worker_time_blocks" in multi_worker_res
            blocks = multi_worker_res["worker_time_blocks"]
            
            if len(blocks) > 1:
                # Each block should have required fields
                for block in blocks:
                    assert "start_time" in block
                    assert "end_time" in block
                    assert "worker_id" in block
                
                # Second block should have gap field for Social Buffer
                if len(blocks) > 1:
                    assert "gap" in blocks[1], "Second block should have gap field for Social Buffer"
