"""Helper: create/cancel TEST_ reservations for UI reschedule tests. usage: seed_ui_resched.py create DATE TIME | cancel ID"""
import os, sys, random, requests
BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
r = requests.post(f"{BASE}/api/auth/login", json={"email": "admin@salon.com", "password": "Admin123!"})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "X-Tenant-ID": "tenant_bsb_001"}
if sys.argv[1] == "create":
    r = requests.post(f"{BASE}/api/admin/reservations", headers=H, json={
        "service_worker_pairs": [{"service_id": "69d3b77e0b47ad8f729e9ba2", "worker_id": "69d4d6f82990ad8a6366bf7d"}],
        "date": sys.argv[2], "time": sys.argv[3], "client_name": "TEST_UIDrag",
        "client_phone": f"+38164{random.randint(1000000, 9999999)}", "force": True})
    print(r.status_code, r.json().get("id"))
elif sys.argv[1] == "cancel":
    print(requests.put(f"{BASE}/api/reservations/{sys.argv[2]}/cancel", headers=H).status_code)
elif sys.argv[1] == "get":
    for x in requests.get(f"{BASE}/api/reservations", headers=H, params={"date": sys.argv[2]}).json():
        if x["client_name"].startswith("TEST_"):
            print(x["id"], x["date"], x["time"], x["worker_name"], x["is_rescheduled"])
