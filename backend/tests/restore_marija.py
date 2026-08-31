"""Utility: restore worker@salon.com (Marija) account to seeded state."""
import asyncio
import os

import bcrypt
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else "https://slot-reserve-23.preview.emergentagent.com"
API = f"{BASE_URL}/api"
TENANT_ID = "tenant_bsb_001"


async def main():
    admin = requests.post(f"{API}/auth/login", json={"email": "admin@salon.com", "password": "Admin123!"}).json()
    hdr = {"Authorization": f"Bearer {admin['access_token']}", "X-Tenant-ID": TENANT_ID}
    workers = requests.get(f"{API}/workers?active_only=false", headers=hdr).json()
    marija = next(w for w in workers if w["name"] == "Marija")
    print("Marija worker_id:", marija["id"])

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    pw_hash = bcrypt.hashpw(b"Worker123!", bcrypt.gensalt()).decode()
    await db.users.delete_many({"email": "worker@salon.com"})
    await db.users.delete_many({"email": "test_milena_qa@salon.com"})
    await db.users.insert_one({
        "email": "worker@salon.com",
        "password_hash": pw_hash,
        "name": "Marija",
        "role": "worker",
        "worker_id": marija["id"],
        "tenant_id": TENANT_ID,
        "language_preference": "sr",
        "must_change_password": False,
        "created_at": "2026-01-01T00:00:00+00:00",
    })
    doc = await db.users.find_one({"email": "worker@salon.com"})
    print("restored, hash prefix:", doc["password_hash"][:4])
    r = requests.post(f"{API}/auth/login", json={"email": "worker@salon.com", "password": "Worker123!"})
    print("worker login status:", r.status_code, r.json().get("role"), r.json().get("worker_id"))
    client.close()


asyncio.run(main())
