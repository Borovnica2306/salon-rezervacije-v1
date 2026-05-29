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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000"), "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRIMARY_TENANT_SLUG = "beauty-studio-bor"
PRIMARY_TENANT_ID = "tenant_bsb_001"


@app.on_event("startup")
async def startup_event():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.services.create_index("category")
    await db.workers.create_index("active")
    await db.reservations.create_index([("date", 1), ("worker_id", 1)])
    await db.blacklisted_phones.create_index("phone")
    await db.tenants.create_index("slug", unique=True)
    await db.tenants.create_index("tenant_id", unique=True)

    # ===== SEED PRIMARY TENANT =====
    existing_tenant = await db.tenants.find_one({"tenant_id": PRIMARY_TENANT_ID})
    if not existing_tenant:
        await db.tenants.insert_one({
            "tenant_id": PRIMARY_TENANT_ID,
            "slug": PRIMARY_TENANT_SLUG,
            "name": "Beauty Studio Bor",
            "owner_email": "bornaja23@gmail.com",
            "country": "RS",
            "city": "Bor",
            "enabled_features": {
                "viber_notifications": True,
                "ips_qr_payment": True,
                "manual_booking": True,
                "email_notifications": True,
                "lazy_cancel": True,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Primary tenant created: {PRIMARY_TENANT_SLUG}")
    else:
        # Migrate existing tenant: add country if missing
        if not existing_tenant.get("country"):
            await db.tenants.update_one(
                {"tenant_id": PRIMARY_TENANT_ID},
                {"$set": {"country": "RS", "city": "Bor"}}
            )

    # ===== SEED SUPER ADMIN =====
    sa_email = "bornaja23@gmail.com"
    sa_password = "Markonijus23!"
    existing_sa = await db.users.find_one({"email": sa_email})
    if not existing_sa:
        await db.users.insert_one({
            "email": sa_email,
            "password_hash": hash_password(sa_password),
            "name": "Super Admin",
            "role": "super_admin",
            "tenant_id": "",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Super-admin created: {sa_email}")
    else:
        update_fields = {}
        if existing_sa.get("role") != "super_admin":
            update_fields["role"] = "super_admin"
        if not verify_password(sa_password, existing_sa["password_hash"]):
            update_fields["password_hash"] = hash_password(sa_password)
        if "tenant_id" not in existing_sa:
            update_fields["tenant_id"] = ""
        if update_fields:
            await db.users.update_one({"email": sa_email}, {"$set": update_fields})
            logger.info(f"Super-admin updated: {sa_email}")

    # ===== SEED SALON ADMIN =====
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@salon.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "admin",
            "tenant_id": PRIMARY_TENANT_ID,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    else:
        update_fields = {}
        if not verify_password(admin_password, existing["password_hash"]):
            update_fields["password_hash"] = hash_password(admin_password)
        if not existing.get("tenant_id"):
            update_fields["tenant_id"] = PRIMARY_TENANT_ID
        if update_fields:
            await db.users.update_one({"email": admin_email}, {"$set": update_fields})
            logger.info(f"Admin updated: {admin_email}")

    # ===== MIGRATE EXISTING DATA: add tenant_id =====
    for coll_name in ["services", "workers", "reservations", "blacklisted_phones", "categories_config"]:
        coll = db[coll_name]
        result = await coll.update_many(
            {"tenant_id": {"$exists": False}},
            {"$set": {"tenant_id": PRIMARY_TENANT_ID}}
        )
        if result.modified_count > 0:
            logger.info(f"Migrated {result.modified_count} docs in '{coll_name}' with tenant_id")

    # Migrate settings
    await db.settings.update_many(
        {"type": "salon", "tenant_id": {"$exists": False}},
        {"$set": {"tenant_id": PRIMARY_TENANT_ID}}
    )

    # Seed categories config if empty
    cat_count = await db.categories_config.count_documents({"tenant_id": PRIMARY_TENANT_ID})
    if cat_count == 0:
        await db.categories_config.insert_many(
            [{"category": k, "enabled": True, "tenant_id": PRIMARY_TENANT_ID} for k in MASTER_CATEGORIES]
        )
        logger.info(f"Seeded {len(MASTER_CATEGORIES)} category configs for tenant")

    # Seed default settings if missing
    settings = await db.settings.find_one({"type": "salon", "tenant_id": PRIMARY_TENANT_ID})
    if not settings:
        await db.settings.insert_one({
            "type": "salon",
            "tenant_id": PRIMARY_TENANT_ID,
            "salon_name": "Beauty Studio Bor",
            "work_start": "09:00",
            "work_end": "21:00",
            "advance_instructions": "Uplata avansa je obavezna 24h pre termina.",
        })

    # Write test credentials
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write("# Test Credentials\n\n")
        f.write("## Super-Admin\n")
        f.write(f"- Email: {sa_email}\n")
        f.write(f"- Password: {sa_password}\n")
        f.write("- Role: super_admin\n\n")
        f.write("## Salon-Admin\n")
        f.write(f"- Email: {admin_email}\n")
        f.write(f"- Password: {admin_password}\n")
        f.write("- Role: admin\n")
        f.write(f"- Tenant: {PRIMARY_TENANT_ID} ({PRIMARY_TENANT_SLUG})\n\n")
        f.write("## Primary Tenant\n")
        f.write(f"- Slug: {PRIMARY_TENANT_SLUG}\n")
        f.write(f"- Tenant ID: {PRIMARY_TENANT_ID}\n")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
