from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
from datetime import datetime, timezone
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from database import db, client, MASTER_CATEGORIES
from auth import hash_password, verify_password
from routes import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI()

# Include the API router
app.include_router(api_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000"), "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.services.create_index("category")
    await db.workers.create_index("active")
    await db.reservations.create_index([("date", 1), ("worker_id", 1)])
    await db.blacklisted_phones.create_index("phone", unique=True)

    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@salon.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")

    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )
        logger.info(f"Admin password updated: {admin_email}")

    # Seed super-admin
    sa_email = "bornaja23@gmail.com"
    sa_password = "Markonijus23!"
    existing_sa = await db.users.find_one({"email": sa_email})
    if not existing_sa:
        await db.users.insert_one({
            "email": sa_email,
            "password_hash": hash_password(sa_password),
            "name": "Super Admin",
            "role": "super_admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Super-admin created: {sa_email}")
    elif existing_sa.get("role") != "super_admin" or not verify_password(sa_password, existing_sa["password_hash"]):
        await db.users.update_one(
            {"email": sa_email},
            {"$set": {"password_hash": hash_password(sa_password), "role": "super_admin"}}
        )
        logger.info(f"Super-admin updated: {sa_email}")

    # Seed categories config
    cat_count = await db.categories_config.count_documents({})
    if cat_count == 0:
        await db.categories_config.insert_many(
            [{"category": k, "enabled": True} for k in MASTER_CATEGORIES]
        )
        logger.info(f"Seeded {len(MASTER_CATEGORIES)} category configs")

    # Seed default settings
    settings = await db.settings.find_one({"type": "salon"})
    if not settings:
        await db.settings.insert_one({
            "type": "salon",
            "salon_name": "Beauty Salon",
            "work_start": "09:00",
            "work_end": "21:00",
            "advance_instructions": "Uplata avansa je obavezna 24h pre termina. Instrukcije za uplatu će vam biti poslate."
        })

    # NO automatic seeding of services or workers
    # All services and workers are managed manually by the admin
    # This prevents any accidental data loss from automated cleanup

    # Write test credentials
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(f"# Test Credentials\n\n")
        f.write(f"## Super-Admin\n")
        f.write(f"- Email: {sa_email}\n")
        f.write(f"- Password: {sa_password}\n")
        f.write(f"- Role: super_admin\n\n")
        f.write(f"## Salon-Admin\n")
        f.write(f"- Email: {admin_email}\n")
        f.write(f"- Password: {admin_password}\n")
        f.write(f"- Role: admin\n\n")
        f.write(f"## Auth Endpoints\n")
        f.write(f"- POST /api/auth/login\n")
        f.write(f"- POST /api/auth/logout\n")
        f.write(f"- GET /api/auth/me\n")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
