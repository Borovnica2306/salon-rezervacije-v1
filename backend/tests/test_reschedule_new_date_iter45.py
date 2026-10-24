"""Iter45: reschedule with new_date, past-date checks, overlap on target date, Pi sandbox payments, CORS."""
import os
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
import requests
from pymongo import MongoClient
from bson import ObjectId

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
TID = "tenant_bsb_001"
WORKER_SUZANA = "69d4d6f82990ad8a6366bf7d"
WORKER_MILENA = "69d4d6f82990ad8a6366bf7e"
SERVICE_SISANJE = "69d3b77e0b47ad8f729e9ba2"

NOW = datetime.now(ZoneInfo("Europe/Belgrade"))
D1 = (NOW + timedelta(days=20)).strftime("%Y-%m-%d")
D2 = (NOW + timedelta(days=21)).strftime("%Y-%m-%d")
YESTERDAY = (NOW - timedelta(days=1)).strftime("%Y-%m-%d")
TODAY = NOW.strftime("%Y-%m-%d")


def _login(email, pw):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}", "X-Tenant-ID": TID}


@pytest.fixture(scope="module")
def admin():
    return _login("admin@salon.com", "Admin123!")


@pytest.fixture(scope="module")
def created(admin):
    ids = []
    yield ids
    for i in ids:
        requests.put(f"{BASE_URL}/api/reservations/{i}/cancel", headers=admin)


def _create(admin, created, date, time, worker=WORKER_SUZANA, phone=None):
    phone = phone or f"+38164{random.randint(1000000, 9999999)}"
    r = requests.post(f"{BASE_URL}/api/admin/reservations", headers=admin, json={
        "service_worker_pairs": [{"service_id": SERVICE_SISANJE, "worker_id": worker}],
        "date": date, "time": time, "client_name": "TEST_Resched", "client_phone": phone, "force": True,
    })
    assert r.status_code == 200, r.text
    rid = r.json()["id"]
    created.append(rid)
    return rid, phone


def _get(admin, date, rid):
    r = requests.get(f"{BASE_URL}/api/reservations", headers=admin, params={"date": date})
    assert r.status_code == 200
    return next((x for x in r.json() if x["id"] == rid), None)


# Reschedule: date change
class TestRescheduleNewDate:
    def test_move_to_new_date_persists(self, admin, created):
        rid, _ = _create(admin, created, D1, "10:00")
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=admin,
                         json={"new_time": "11:00", "new_worker_id": WORKER_MILENA, "new_date": D2})
        assert r.status_code == 200, r.text
        assert r.json()["new_date"] == D2
        assert _get(admin, D1, rid) is None
        moved = _get(admin, D2, rid)
        assert moved and moved["time"] == "11:00" and moved["worker_id"] == WORKER_MILENA
        assert moved["is_rescheduled"] is True

    def test_without_new_date_keeps_date(self, admin, created):
        rid, _ = _create(admin, created, D1, "12:00")
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=admin,
                         json={"new_time": "12:30", "new_worker_id": WORKER_SUZANA})
        assert r.status_code == 200, r.text
        assert r.json()["new_date"] == D1
        assert _get(admin, D1, rid)["time"] == "12:30"

    def test_invalid_date_400(self, admin, created):
        rid, _ = _create(admin, created, D1, "13:00")
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=admin,
                         json={"new_time": "13:00", "new_worker_id": WORKER_SUZANA, "new_date": "2026-13-45"})
        assert r.status_code == 400

    def test_worker_overlap_on_target_date(self, admin, created):
        _create(admin, created, D2, "15:00", worker=WORKER_SUZANA)
        rid, _ = _create(admin, created, D1, "15:00", worker=WORKER_SUZANA)
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=admin,
                         json={"new_time": "15:00", "new_worker_id": WORKER_SUZANA, "new_date": D2})
        assert r.status_code == 400 and "zauzet" in r.json()["detail"]

    def test_client_overlap_on_target_date(self, admin, created):
        _, phone = _create(admin, created, D2, "16:00", worker=WORKER_MILENA)
        rid, _ = _create(admin, created, D1, "16:00", worker=WORKER_SUZANA, phone=phone)
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=admin,
                         json={"new_time": "16:00", "new_worker_id": WORKER_SUZANA, "new_date": D2})
        assert r.status_code == 400 and "Klijent" in r.json()["detail"]


# Reschedule: past checks
class TestReschedulePast:
    def test_move_into_past_day(self, admin, created):
        rid, _ = _create(admin, created, D1, "17:00")
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=admin,
                         json={"new_time": "10:00", "new_worker_id": WORKER_SUZANA, "new_date": YESTERDAY})
        assert r.status_code == 400
        assert r.json()["detail"] == "Nije moguće premestiti rezervaciju u prošlost."

    def test_move_into_past_time_today(self, admin, created):
        if NOW.hour < 1:
            pytest.skip("too early")
        rid, _ = _create(admin, created, D1, "17:30")
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=admin,
                         json={"new_time": "00:00", "new_worker_id": WORKER_SUZANA, "new_date": TODAY})
        assert r.status_code == 400
        assert "prošlost" in r.json()["detail"]

    def test_move_reservation_from_past_day(self, admin, created):
        rid, _ = _create(admin, created, D1, "18:00")
        # force original date into the past directly in DB
        mc = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        dbn = os.environ.get("DB_NAME")
        if not dbn:
            for line in open("/app/backend/.env"):
                if line.startswith("DB_NAME"):
                    dbn = line.split("=", 1)[1].strip().strip('"')
        mc[dbn].reservations.update_one({"_id": ObjectId(rid)}, {"$set": {"date": YESTERDAY}})
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=admin,
                         json={"new_time": "10:00", "new_worker_id": WORKER_SUZANA, "new_date": D2})
        assert r.status_code == 400
        assert "prošlog dana" in r.json()["detail"]

    def test_worker_role_cannot_reschedule(self, admin, created):
        rid, _ = _create(admin, created, D1, "19:00")
        w = _login("worker@salon.com", "Worker123!")
        r = requests.put(f"{BASE_URL}/api/reservations/{rid}/reschedule", headers=w,
                         json={"new_time": "19:30", "new_worker_id": WORKER_SUZANA, "new_date": D1})
        assert r.status_code == 403, f"worker was able to reschedule: {r.status_code} {r.text}"

    def test_invalid_reservation_id(self, admin):
        r = requests.put(f"{BASE_URL}/api/reservations/notanid/reschedule", headers=admin,
                         json={"new_time": "10:00", "new_worker_id": WORKER_SUZANA, "new_date": D1})
        assert r.status_code in (400, 404, 422), r.status_code


# Pi sandbox payments
class TestPiPayments:
    def test_approve_sandbox(self):
        r = requests.post(f"{BASE_URL}/api/payments/approve", headers={"X-Tenant-ID": TID},
                          json={"paymentId": "TEST_p1", "booking_id": "TEST_b1", "is_sandbox": True})
        assert r.status_code == 200 and r.json()["status"] == "approved"

    def test_complete_sandbox(self):
        r = requests.post(f"{BASE_URL}/api/payments/complete", headers={"X-Tenant-ID": TID},
                          json={"paymentId": "TEST_p1", "txid": "x", "booking_id": "TEST_b1", "is_sandbox": True})
        assert r.status_code == 200 and r.json()["status"] == "completed"

    def test_missing_fields_400(self):
        r = requests.post(f"{BASE_URL}/api/payments/approve", json={"is_sandbox": True})
        assert r.status_code == 400


# CORS from FRONTEND_URL
class TestCORS:
    @pytest.mark.parametrize("origin", [BASE_URL, "https://salon-rezervacije-v1-5wyy.vercel.app"])
    def test_allowed_origin(self, origin):
        r = requests.options(f"{BASE_URL}/api/auth/login", headers={
            "Origin": origin, "Access-Control-Request-Method": "POST"})
        assert r.headers.get("access-control-allow-origin") == origin
        assert r.headers.get("access-control-allow-credentials") == "true"

    def test_disallowed_origin(self):
        r = requests.options(f"{BASE_URL}/api/auth/login", headers={
            "Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"})
        assert r.headers.get("access-control-allow-origin") != "https://evil.example.com"
