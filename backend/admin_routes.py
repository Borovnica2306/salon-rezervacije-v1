"""
Admin routes: tenant resolution, super-admin CRUD, categories, services, blacklist, settings, reminders.
"""
import re
import uuid
import jwt
import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from bson import ObjectId
from typing import List
from datetime import datetime, timezone

from database import db, MASTER_CATEGORIES
from models import (
    ServiceCreate, ServiceUpdate, ServiceResponse,
    SettingsUpdate, SettingsResponse, CategoryToggle,
)
from auth import (
    get_jwt_secret, JWT_ALGORITHM, hash_password, get_current_user,
)
from logic import (
    normalize_phone, get_enabled_categories, process_daily_reminders,
)
from tenant import check_tenant_access
from route_utils import _get_tid

logger = logging.getLogger(__name__)

router = APIRouter()


# ================== TENANT RESOLUTION ==================

@router.get("/tenants/by-slug/{slug}")
async def get_tenant_by_slug(slug: str):
    tenant = await db.tenants.find_one({"slug": slug})
    if not tenant:
        raise HTTPException(status_code=404, detail="Salon not found")
    return {
        "tenant_id": tenant["tenant_id"],
        "slug": tenant["slug"],
        "name": tenant["name"],
        "country": tenant.get("country", "RS"),
        "city": tenant.get("city", ""),
        "enabled_features": tenant.get("enabled_features", {}),
        "theme": tenant.get("theme", "MidnightVelvet"),
    }


@router.get("/tenants/by-country/{country_code}")
async def get_tenants_by_country(country_code: str):
    tenants = await db.tenants.find(
        {"country": country_code.upper()},
        {"_id": 0, "tenant_id": 1, "slug": 1, "name": 1, "country": 1, "city": 1}
    ).to_list(100)
    return tenants


# ================== SUPER ADMIN: TENANT MANAGEMENT ==================

@router.get("/super/tenants")
async def list_tenants(user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
    return tenants


@router.put("/super/tenants/{tenant_id}/features")
async def update_tenant_features(tenant_id: str, features: dict, user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    tenant = await db.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    await db.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"enabled_features": features}}
    )
    updated = await db.tenants.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return updated


@router.put("/super/tenants/{tenant_id}/name")
async def update_tenant_name(tenant_id: str, body: dict, user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name required")
    await db.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"name": name}}
    )
    return {"name": name}


@router.put("/super/tenants/{tenant_id}/theme")
async def update_tenant_theme(tenant_id: str, body: dict, user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    tenant = await db.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    theme = body.get("theme", "MidnightVelvet").strip()
    await db.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"theme": theme}}
    )
    return {"tenant_id": tenant_id, "theme": theme}


@router.put("/super/tenants/{tenant_id}/status")
async def update_tenant_status(tenant_id: str, body: dict, user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    tenant = await db.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    status = body.get("status", "").strip()
    if status not in ("active", "suspended"):
        raise HTTPException(status_code=400, detail="Status must be 'active' or 'suspended'")
    await db.tenants.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"status": status}}
    )
    return {"tenant_id": tenant_id, "status": status}


@router.put("/super/tenants/{tenant_id}/owner-password")
async def update_owner_password(tenant_id: str, body: dict, user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    tenant = await db.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    new_password = body.get("password", "").strip()
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    owner_email = tenant.get("owner_email", "")
    if not owner_email:
        raise HTTPException(status_code=400, detail="Tenant has no owner email")
    target_user = await db.users.find_one({"email": owner_email})
    if not target_user:
        raise HTTPException(status_code=404, detail="Owner user not found")
    if target_user.get("role") == "super_admin":
        raise HTTPException(status_code=403, detail="Ne možete menjati lozinku Super Admin naloga kroz ovaj panel")
    result = await db.users.update_one(
        {"email": owner_email},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Owner user not found")
    return {"message": "Password updated", "email": owner_email}


@router.post("/super/tenants")
async def create_tenant(body: dict, user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")

    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "").strip()
    country = body.get("country", "RS").upper()
    city = body.get("city", "").strip()

    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Name, email and password are required")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    slug = name.lower().strip()
    slug = slug.replace("š", "s").replace("č", "c").replace("ć", "c").replace("ž", "z").replace("đ", "dj")
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug).strip('-')

    existing_slug = await db.tenants.find_one({"slug": slug})
    if existing_slug:
        slug = f"{slug}-{str(ObjectId())[:6]}"

    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with email {email} already exists")

    tenant_id = f"tenant_{slug.replace('-', '_')[:20]}_{uuid.uuid4().hex[:8]}"

    await db.tenants.insert_one({
        "tenant_id": tenant_id,
        "slug": slug,
        "name": name,
        "owner_email": email,
        "country": country,
        "city": city,
        "enabled_features": {
            "manual_booking": True,
            "email_notifications": True,
            "lazy_cancel": True,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    await db.users.insert_one({
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "role": "admin",
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    await db.settings.insert_one({
        "type": "salon",
        "tenant_id": tenant_id,
        "salon_name": name,
        "work_start": "09:00",
        "work_end": "21:00",
        "advance_instructions": "",
    })

    await db.categories_config.insert_many(
        [{"category": k, "enabled": True, "tenant_id": tenant_id} for k in MASTER_CATEGORIES]
    )

    logger.info(f"New tenant created: {slug} ({tenant_id}) by super admin")

    return {
        "tenant_id": tenant_id,
        "slug": slug,
        "name": name,
        "country": country,
        "city": city,
        "admin_email": email,
    }


# ================== CATEGORIES CONFIG ENDPOINTS ==================

@router.get("/categories")
async def get_categories(request: Request):
    tid = await _get_tid(request)
    enabled = await get_enabled_categories(tid)
    return [{"key": k, "label": MASTER_CATEGORIES[k]} for k in enabled if k in MASTER_CATEGORIES]


@router.get("/categories/config")
async def get_categories_config(request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)
    configs = await db.categories_config.find({"tenant_id": tid}, {"_id": 0}).to_list(100)
    config_map = {c["category"]: c["enabled"] for c in configs}
    return [
        {"key": k, "label": v, "enabled": config_map.get(k, True)}
        for k, v in MASTER_CATEGORIES.items()
    ]


@router.put("/categories/config")
async def update_category_config(toggle: CategoryToggle, request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)
    if toggle.category not in MASTER_CATEGORIES:
        raise HTTPException(status_code=400, detail="Nepoznata kategorija")
    await db.categories_config.update_one(
        {"category": toggle.category, "tenant_id": tid},
        {"$set": {"category": toggle.category, "enabled": toggle.enabled, "tenant_id": tid}},
        upsert=True
    )
    return {"category": toggle.category, "enabled": toggle.enabled}


# ================== SERVICES ENDPOINTS ==================

@router.get("/services", response_model=List[ServiceResponse])
async def get_services(active_only: bool = True, request: Request = None):
    tid = request.headers.get("X-Tenant-ID", "") if request else ""
    query = {"tenant_id": tid}
    if active_only:
        query["active"] = True

    try:
        token = request.cookies.get("access_token") if request else None
        if not token:
            auth_header = request.headers.get("Authorization", "") if request else ""
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        if token:
            payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
            usr = await db.users.find_one({"_id": ObjectId(payload["sub"])})
            if usr and usr.get("role") == "super_admin":
                pass
            elif usr and usr.get("role") in ("admin",):
                if "active" in query:
                    del query["active"]
    except Exception:
        pass

    services = await db.services.find(query, {"_id": 1, "name": 1, "category": 1, "duration": 1, "price": 1, "description": 1, "active": 1}).to_list(100)
    return [
        ServiceResponse(
            id=str(s["_id"]),
            name=s["name"],
            category=s["category"],
            duration=s["duration"],
            price=s["price"],
            description=s.get("description", ""),
            active=s.get("active", True)
        ) for s in services
    ]


@router.post("/services", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    doc = {
        "name": service.name,
        "category": service.category,
        "duration": service.duration,
        "price": service.price,
        "description": service.description or "",
        "active": True,
        "tenant_id": tid,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.services.insert_one(doc)
    return ServiceResponse(id=str(result.inserted_id), **{k: v for k, v in doc.items() if k not in ["created_at", "_id", "tenant_id"]})


@router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, update: ServiceUpdate, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    result = await db.services.find_one_and_update(
        {"_id": ObjectId(service_id)},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Service not found")

    return ServiceResponse(
        id=str(result["_id"]),
        name=result["name"],
        category=result["category"],
        duration=result["duration"],
        price=result["price"],
        description=result.get("description", ""),
        active=result.get("active", True)
    )


@router.delete("/services/{service_id}")
async def delete_service(service_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    service = await db.services.find_one({"_id": ObjectId(service_id)})
    if not service:
        raise HTTPException(status_code=404, detail="Usluga nije pronađena.")

    await db.services.delete_one({"_id": ObjectId(service_id)})
    return {"message": "Usluga je trajno obrisana."}


# ================== BLACKLIST ENDPOINTS ==================

@router.get("/blacklist")
async def get_blacklist(request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin", "worker"):
        raise HTTPException(status_code=403, detail="Admin access required")

    phones = await db.blacklisted_phones.find({"tenant_id": tid}, {"_id": 0}).to_list(1000)
    return phones


@router.post("/blacklist")
async def add_to_blacklist(phone: str, request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    phone = normalize_phone(phone.strip())
    existing = await db.blacklisted_phones.find_one({"phone": phone, "tenant_id": tid})
    if existing:
        return {"message": "Phone already blacklisted"}

    await db.blacklisted_phones.insert_one({
        "phone": phone,
        "tenant_id": tid,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    logger.info(f"Phone added to blacklist: {phone}")
    return {"message": "Phone added to blacklist"}


@router.delete("/blacklist/{phone}")
async def remove_from_blacklist(phone: str, request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    phone = normalize_phone(phone)
    await db.blacklisted_phones.delete_one({"phone": phone, "tenant_id": tid})
    return {"message": "Phone removed from blacklist"}


# ================== SETTINGS ENDPOINTS ==================

@router.get("/settings", response_model=SettingsResponse)
async def get_settings(request: Request):
    tid = request.headers.get("X-Tenant-ID", "")
    settings = await db.settings.find_one({"type": "salon", "tenant_id": tid})
    if not settings:
        return SettingsResponse(
            salon_name="Beauty Salon",
            work_start="09:00",
            work_end="21:00",
            advance_instructions="Uplata avansa je obavezna 24h pre termina. Instrukcije za uplatu će vam biti poslate.",
        )
    return SettingsResponse(
        salon_name=settings.get("salon_name", "Beauty Salon"),
        work_start=settings.get("work_start", "09:00"),
        work_end=settings.get("work_end", "21:00"),
        advance_instructions=settings.get("advance_instructions", ""),
        pi_wallet_address=settings.get("pi_wallet_address", ""),
        smtp_server=settings.get("smtp_server", "smtp.gmail.com"),
        smtp_port=settings.get("smtp_port", 587),
        smtp_user=settings.get("smtp_user", ""),
        smtp_password=settings.get("smtp_password", ""),
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate, request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    PROTECTED_FIELDS = {"smtp_server", "smtp_port", "smtp_user", "smtp_password", "salon_name"}
    if user.get("role") != "super_admin":
        has_protected = PROTECTED_FIELDS & set(update_data.keys())
        if has_protected:
            raise HTTPException(status_code=403, detail="Only Super Admin can modify integration settings")
        for f in PROTECTED_FIELDS:
            update_data.pop(f, None)

    update_data["type"] = "salon"
    update_data["tenant_id"] = tid

    await db.settings.update_one(
        {"type": "salon", "tenant_id": tid},
        {"$set": update_data},
        upsert=True
    )

    settings = await db.settings.find_one({"type": "salon", "tenant_id": tid})
    return SettingsResponse(
        salon_name=settings.get("salon_name", "Beauty Salon"),
        work_start=settings.get("work_start", "09:00"),
        work_end=settings.get("work_end", "21:00"),
        advance_instructions=settings.get("advance_instructions", ""),
        pi_wallet_address=settings.get("pi_wallet_address", ""),
        smtp_server=settings.get("smtp_server", "smtp.gmail.com"),
        smtp_port=settings.get("smtp_port", 587),
        smtp_user=settings.get("smtp_user", ""),
        smtp_password=settings.get("smtp_password", ""),
    )


# ================== REMINDERS ==================

@router.post("/admin/reservations/trigger-reminders")
async def trigger_reminders(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    tid = await _get_tid(request)
    result = await process_daily_reminders(tid)
    return result


# ================== ROOT ENDPOINT ==================

@router.get("/")
async def root():
    return {"message": "Salon Booking API"}
