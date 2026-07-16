import jwt
import os
import logging
import httpx
from fastapi import APIRouter, HTTPException, Request, Response, Depends, BackgroundTasks, Header
from bson import ObjectId
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from database import db, MASTER_CATEGORIES
from models import (
    LoginRequest, ServiceCreate, ServiceUpdate, ServiceResponse,
    WorkerCreate, WorkerUpdate, WorkerResponse, ServiceWorkerPair,
    ReservationCreate, ReservationResponse, SettingsUpdate, SettingsResponse,
    AvailableSlotsRequest, CategoryToggle, ClientReservationsRequest,
    AdminReservationCreate,
)
from auth import (
    get_jwt_secret, JWT_ALGORITHM, hash_password, verify_password,
    create_access_token, create_refresh_token, get_current_user,
)
from logic import (
    time_to_minutes, minutes_to_time, normalize_phone,
    generate_booking_id, get_enabled_categories, can_client_cancel,
    get_available_slots_multi, cancel_stale_unpaid_reservations,
    process_daily_reminders,
)
from mail_service import send_booking_confirmation_email, PAYMENT_MODE
from tenant import resolve_tenant_by_slug, check_tenant_access

logger = logging.getLogger(__name__)

PI_API_KEY = os.environ.get("PI_API_KEY", "")
PI_API_BASE = "https://api.minepi.com/v2"

api_router = APIRouter(prefix="/api")


async def _get_tid(request: Request) -> str:
    """Extract tenant_id from X-Tenant-ID header."""
    tid = request.headers.get("X-Tenant-ID", "")
    if not tid:
        raise HTTPException(status_code=400, detail="Missing X-Tenant-ID header")
    return tid


async def _get_tid_optional(request: Request) -> str:
    """Extract tenant_id, return empty string if missing."""
    return request.headers.get("X-Tenant-ID", "")


# ================== TENANT RESOLUTION ==================

@api_router.get("/tenants/by-slug/{slug}")
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


@api_router.get("/tenants/by-country/{country_code}")
async def get_tenants_by_country(country_code: str):
    tenants = await db.tenants.find(
        {"country": country_code.upper()},
        {"_id": 0, "tenant_id": 1, "slug": 1, "name": 1, "country": 1, "city": 1}
    ).to_list(100)
    return tenants


# ================== SUPER ADMIN: TENANT MANAGEMENT ==================

@api_router.get("/super/tenants")
async def list_tenants(user: dict = Depends(get_current_user)):
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
    return tenants


@api_router.put("/super/tenants/{tenant_id}/features")
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


@api_router.put("/super/tenants/{tenant_id}/name")
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


@api_router.put("/super/tenants/{tenant_id}/theme")
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


@api_router.put("/super/tenants/{tenant_id}/status")
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


@api_router.put("/super/tenants/{tenant_id}/owner-password")
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
    # Guard: prevent changing super_admin password via this endpoint
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


@api_router.post("/super/tenants")
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

    # Generate slug from name
    import re
    slug = name.lower().strip()
    slug = slug.replace("š", "s").replace("č", "c").replace("ć", "c").replace("ž", "z").replace("đ", "dj")
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug).strip('-')

    # Ensure slug is unique
    existing_slug = await db.tenants.find_one({"slug": slug})
    if existing_slug:
        slug = f"{slug}-{str(ObjectId())[:6]}"

    # Ensure email is unique
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User with email {email} already exists")

    # Generate tenant_id
    import uuid
    tenant_id = f"tenant_{slug.replace('-', '_')[:20]}_{uuid.uuid4().hex[:8]}"

    # Create tenant
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

    # Create admin user for this tenant
    await db.users.insert_one({
        "email": email,
        "password_hash": hash_password(password),
        "name": name,
        "role": "admin",
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Seed default settings
    await db.settings.insert_one({
        "type": "salon",
        "tenant_id": tenant_id,
        "salon_name": name,
        "work_start": "09:00",
        "work_end": "21:00",
        "advance_instructions": "",
    })

    # Seed categories
    from database import MASTER_CATEGORIES
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

@api_router.get("/categories")
async def get_categories(request: Request):
    tid = await _get_tid(request)
    enabled = await get_enabled_categories(tid)
    return [{"key": k, "label": MASTER_CATEGORIES[k]} for k in enabled if k in MASTER_CATEGORIES]


@api_router.get("/categories/config")
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


@api_router.put("/categories/config")
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


# ================== AUTH ENDPOINTS ==================

@api_router.post("/auth/login")
async def login(request: LoginRequest, response: Response):
    email = request.email.lower().strip()
    user = await db.users.find_one({"email": email})

    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    tenant_id = user.get("tenant_id", "")
    role = user.get("role", "admin")
    access_token = create_access_token(user_id, email, tenant_id, role)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    # Resolve slug for smart redirect
    slug = ""
    if tenant_id:
        tenant = await db.tenants.find_one({"tenant_id": tenant_id}, {"slug": 1})
        if tenant:
            slug = tenant["slug"]

    return {
        "id": user_id,
        "email": user["email"],
        "name": user["name"],
        "role": role,
        "tenant_id": tenant_id,
        "slug": slug,
        "access_token": access_token
    }


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}


@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    # Add slug for frontend redirect
    tenant_id = user.get("tenant_id", "")
    if tenant_id and not user.get("slug"):
        tenant = await db.tenants.find_one({"tenant_id": tenant_id}, {"slug": 1})
        if tenant:
            user["slug"] = tenant["slug"]
    return user


# ================== SERVICES ENDPOINTS ==================

@api_router.get("/services", response_model=List[ServiceResponse])
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


@api_router.post("/services", response_model=ServiceResponse)
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


@api_router.put("/services/{service_id}", response_model=ServiceResponse)
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


@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    service = await db.services.find_one({"_id": ObjectId(service_id)})
    if not service:
        raise HTTPException(status_code=404, detail="Usluga nije pronađena.")

    await db.services.delete_one({"_id": ObjectId(service_id)})
    return {"message": "Usluga je trajno obrisana."}


# ================== WORKERS ENDPOINTS ==================

@api_router.get("/workers", response_model=List[WorkerResponse])
async def get_workers(request: Request, active_only: bool = True):
    tid = await _get_tid(request)
    query = {"tenant_id": tid}
    if active_only:
        query["active"] = True
    workers = await db.workers.find(query).to_list(100)
    return [
        WorkerResponse(
            id=str(w["_id"]),
            name=w["name"],
            services=w.get("services", []),
            work_start=w.get("work_start", "09:00"),
            work_end=w.get("work_end", "21:00"),
            break_start=w.get("break_start"),
            break_end=w.get("break_end"),
            days_off=w.get("days_off", []),
            active=w.get("active", True)
        ) for w in workers
    ]


@api_router.post("/workers", response_model=WorkerResponse)
async def create_worker(worker: WorkerCreate, request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    doc = {
        "name": worker.name,
        "services": worker.services,
        "work_start": worker.work_start,
        "work_end": worker.work_end,
        "break_start": worker.break_start,
        "break_end": worker.break_end,
        "days_off": worker.days_off,
        "active": True,
        "tenant_id": tid,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.workers.insert_one(doc)
    return WorkerResponse(id=str(result.inserted_id), **{k: v for k, v in doc.items() if k not in ["created_at", "_id", "tenant_id"]})


@api_router.put("/workers/{worker_id}", response_model=WorkerResponse)
async def update_worker(worker_id: str, update: WorkerUpdate, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    result = await db.workers.find_one_and_update(
        {"_id": ObjectId(worker_id)},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Worker not found")

    return WorkerResponse(
        id=str(result["_id"]),
        name=result["name"],
        services=result.get("services", []),
        work_start=result.get("work_start", "09:00"),
        work_end=result.get("work_end", "21:00"),
        break_start=result.get("break_start"),
        break_end=result.get("break_end"),
        days_off=result.get("days_off", []),
        active=result.get("active", True)
    )


@api_router.delete("/workers/{worker_id}")
async def delete_worker(worker_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    worker = await db.workers.find_one({"_id": ObjectId(worker_id)})
    if not worker:
        raise HTTPException(status_code=404, detail="Radnik nije pronađen.")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    future_count = await db.reservations.count_documents({
        "status": {"$ne": "cancelled"},
        "date": {"$gte": today},
        "$or": [
            {"worker_id": worker_id},
            {"service_worker_pairs.worker_id": worker_id},
            {"worker_time_blocks.worker_id": worker_id}
        ]
    })

    if future_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Nije moguće obrisati radnika koji ima zakazane termine. Prvo otkažite ili premestite termine."
        )

    await db.workers.delete_one({"_id": ObjectId(worker_id)})
    return {"message": "Radnik je trajno obrisan."}


# ================== RESERVATIONS ENDPOINTS ==================

@api_router.post("/reservations/available-slots")
async def get_slots(request_body: AvailableSlotsRequest, request: Request):
    tid = await _get_tid(request)
    await cancel_stale_unpaid_reservations(tid)
    pairs = [{"service_id": p.service_id, "worker_id": p.worker_id} for p in request_body.service_worker_pairs]
    return await get_available_slots_multi(pairs, request_body.date, tid)


@api_router.post("/reservations", response_model=ReservationResponse)
async def create_reservation(reservation: ReservationCreate, request: Request, background_tasks: BackgroundTasks):
    tid = await _get_tid(request)
    phone = normalize_phone(reservation.client_phone.strip())

    # Check if phone is blacklisted
    blacklisted = await db.blacklisted_phones.find_one({"phone": phone, "tenant_id": tid})
    if blacklisted:
        logger.info(f"Blocked phone attempted to book: {phone}")
        raise HTTPException(status_code=403, detail="Ovaj broj telefona je blokiran za rezervacije.")

    # Check daily limit (max 3 per phone per day)
    today_count = await db.reservations.count_documents({
        "client_phone": phone,
        "date": reservation.date,
        "status": {"$ne": "cancelled"},
        "tenant_id": tid,
    })
    logger.info(f"Phone {phone} has {today_count} reservations for date {reservation.date}")
    if today_count >= 3:
        raise HTTPException(status_code=400, detail="Maksimalno 3 rezervacije dnevno po broju telefona.")

    # Hard limit: block bookings within 2 hours for today (Belgrade time)
    belgrade_tz = timezone(timedelta(hours=2))
    now_belgrade = datetime.now(belgrade_tz)
    today_belgrade = now_belgrade.strftime("%Y-%m-%d")
    if reservation.date == today_belgrade:
        now_minutes = now_belgrade.hour * 60 + now_belgrade.minute
        slot_minutes = time_to_minutes(reservation.time)
        if slot_minutes < now_minutes + 120:
            raise HTTPException(status_code=400, detail="Nije moguće zakazati termin koji počinje za manje od 2 sata.")

    # Get all service IDs from pairs
    service_ids = [p.service_id for p in reservation.service_worker_pairs]
    worker_ids = [p.worker_id for p in reservation.service_worker_pairs]

    # Get services and calculate totals
    service_docs = await db.services.find({
        "_id": {"$in": [ObjectId(s) for s in service_ids]},
        "active": True,
        "tenant_id": tid
    }).to_list(100)

    if len(service_docs) != len(service_ids):
        raise HTTPException(status_code=400, detail="Neke izabrane usluge nisu dostupne.")

    service_map = {str(s["_id"]): s for s in service_docs}

    total_duration = sum(s["duration"] for s in service_docs)
    total_price = sum(s["price"] for s in service_docs)

    # Get workers
    workers = await db.workers.find({
        "_id": {"$in": [ObjectId(w) for w in worker_ids]},
        "active": True,
        "tenant_id": tid,
    }).to_list(100)

    if len(workers) != len(set(worker_ids)):
        raise HTTPException(status_code=400, detail="Neki izabrani radnici nisu dostupni.")

    worker_map = {str(w["_id"]): w for w in workers}

    # Build service_worker_pairs with names
    service_worker_pairs = []
    service_names = []
    for p in reservation.service_worker_pairs:
        srv = service_map.get(p.service_id)
        wrk = worker_map.get(p.worker_id)
        if srv and wrk:
            service_worker_pairs.append({
                "service_id": p.service_id,
                "service_name": srv["name"],
                "worker_id": p.worker_id,
                "worker_name": wrk["name"],
                "duration": srv["duration"],
                "price": srv["price"]
            })
            service_names.append(srv["name"])

    # Verify slot is still available and get slot details
    pairs_dict = [{"service_id": p.service_id, "worker_id": p.worker_id} for p in reservation.service_worker_pairs]
    available = await get_available_slots_multi(pairs_dict, reservation.date, tid)
    if reservation.time not in available.get("slots", []):
        raise HTTPException(status_code=400, detail="Izabrani termin više nije dostupan.")

    # Get detailed slot info for accurate end_time and worker_time_blocks
    slot_detail = available.get("slot_details", {}).get(reservation.time, {})

    # Calculate end time from slot details (includes gaps) or fallback
    if slot_detail:
        end_time = slot_detail["end_time"]
        actual_duration = slot_detail["total_duration"]
        worker_time_blocks = slot_detail.get("time_blocks", [])
    else:
        start_minutes = time_to_minutes(reservation.time)
        end_time = minutes_to_time(start_minutes + total_duration)
        actual_duration = total_duration
        worker_time_blocks = []

    # --- Anti-Conflict: Prevent client from double-booking overlapping times ---
    existing_client_reservations = await db.reservations.find({
        "client_phone": phone,
        "date": reservation.date,
        "status": {"$ne": "cancelled"},
        "tenant_id": tid,
    }).to_list(100)

    if existing_client_reservations:
        new_ranges = []
        if worker_time_blocks:
            for block in worker_time_blocks:
                new_ranges.append((
                    time_to_minutes(block["start_time"]),
                    time_to_minutes(block["end_time"])
                ))
        else:
            new_ranges.append((
                time_to_minutes(reservation.time),
                time_to_minutes(end_time)
            ))

        for existing_res in existing_client_reservations:
            existing_ranges = []
            if "worker_time_blocks" in existing_res and existing_res["worker_time_blocks"]:
                for block in existing_res["worker_time_blocks"]:
                    existing_ranges.append((
                        time_to_minutes(block["start_time"]),
                        time_to_minutes(block["end_time"])
                    ))
            else:
                existing_ranges.append((
                    time_to_minutes(existing_res["time"]),
                    time_to_minutes(existing_res["end_time"])
                ))

            for new_start, new_end in new_ranges:
                for ex_start, ex_end in existing_ranges:
                    if new_start < ex_end and ex_start < new_end:
                        raise HTTPException(
                            status_code=409,
                            detail="Već imate rezervaciju koja se preklapa sa ovim terminom. Molimo izaberite drugo vreme."
                        )

    # Get first worker for legacy compatibility
    first_worker_id = worker_ids[0] if worker_ids else None
    first_worker = worker_map.get(first_worker_id, {})

    # Generate short booking ID
    booking_id = await generate_booking_id()

    doc = {
        "booking_id": booking_id,
        "services": service_ids,
        "service_names": service_names,
        "service_worker_pairs": service_worker_pairs,
        "worker_time_blocks": worker_time_blocks,
        "worker_id": first_worker_id,
        "worker_name": first_worker.get("name", ""),
        "date": reservation.date,
        "time": reservation.time,
        "end_time": end_time,
        "total_duration": actual_duration,
        "total_price": total_price,
        "client_name": reservation.client_name,
        "client_phone": phone,
        "client_email": reservation.client_email.strip().lower(),
        "pi_username": reservation.pi_username or "",
        "pi_uid": reservation.pi_uid or "",
        "status": "confirmed",
        "payment_status": "pending_pi_payment" if PAYMENT_MODE == "PI_ECOSYSTEM" else "pending",
        "advance_required": True,
        "advance_released": False,
        "tenant_id": tid,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    result = await db.reservations.insert_one(doc)

    # Send confirmation email in background
    settings_doc = await db.settings.find_one({"type": "salon", "tenant_id": tid})
    salon_name = settings_doc.get("salon_name", "Beauty Salon") if settings_doc else "Beauty Salon"
    client_email = reservation.client_email.strip().lower()

    logger.info(f"[BOOKING] #{booking_id} created for {reservation.client_name}, email from form: {client_email}")

    if client_email:
        background_tasks.add_task(
            send_booking_confirmation_email,
            to_email=client_email,
            salon_name=salon_name,
            booking_id=booking_id,
            client_name=reservation.client_name,
            date=reservation.date,
            time=reservation.time,
            end_time=end_time,
            service_worker_pairs=service_worker_pairs,
            total_price=total_price,
            total_duration=actual_duration,
        )

    return ReservationResponse(
        id=str(result.inserted_id),
        booking_id=booking_id,
        services=service_ids,
        service_names=service_names,
        service_worker_pairs=service_worker_pairs,
        worker_time_blocks=worker_time_blocks,
        worker_id=first_worker_id,
        worker_name=first_worker.get("name", ""),
        date=reservation.date,
        time=reservation.time,
        end_time=end_time,
        total_duration=actual_duration,
        total_price=total_price,
        client_name=reservation.client_name,
        client_phone=phone,
        client_email=reservation.client_email.strip().lower(),
        pi_username=reservation.pi_username or "",
        pi_uid=reservation.pi_uid or "",
        status="confirmed",
        payment_status="pending_pi_payment" if PAYMENT_MODE == "PI_ECOSYSTEM" else "pending",
        advance_required=True,
        advance_released=False,
        created_at=doc["created_at"]
    )


@api_router.post("/admin/reservations", response_model=ReservationResponse)
async def admin_create_reservation(
    reservation: AdminReservationCreate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Admin manual booking - can force-create even with conflicts."""
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    tid = await _get_tid(request)
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    phone = normalize_phone(reservation.client_phone.strip())

    # Check daily limit (max 3 per phone per day) - still enforced for admin
    today_count = await db.reservations.count_documents({
        "client_phone": phone,
        "date": reservation.date,
        "status": {"$ne": "cancelled"},
        "tenant_id": tid,
    })

    # Get all service IDs from pairs
    service_ids = [p.service_id for p in reservation.service_worker_pairs]
    worker_ids = [p.worker_id for p in reservation.service_worker_pairs]

    # Get services and calculate totals
    service_docs = await db.services.find({
        "_id": {"$in": [ObjectId(s) for s in service_ids]},
        "active": True,
        "tenant_id": tid,
    }).to_list(100)

    if len(service_docs) != len(service_ids):
        raise HTTPException(status_code=400, detail="Neke izabrane usluge nisu dostupne.")

    service_map = {str(s["_id"]): s for s in service_docs}
    total_duration = sum(s["duration"] for s in service_docs)
    total_price = sum(s["price"] for s in service_docs)

    # Get workers
    workers_list = await db.workers.find({
        "_id": {"$in": [ObjectId(w) for w in worker_ids]},
        "active": True,
        "tenant_id": tid,
    }).to_list(100)

    if len(workers_list) != len(set(worker_ids)):
        raise HTTPException(status_code=400, detail="Neki izabrani radnici nisu dostupni.")

    worker_map = {str(w["_id"]): w for w in workers_list}

    # Build service_worker_pairs with names
    swp = []
    service_names = []
    for p in reservation.service_worker_pairs:
        srv = service_map.get(p.service_id)
        wrk = worker_map.get(p.worker_id)
        if srv and wrk:
            swp.append({
                "service_id": p.service_id,
                "service_name": srv["name"],
                "worker_id": p.worker_id,
                "worker_name": wrk["name"],
                "duration": srv["duration"],
                "price": srv["price"]
            })
            service_names.append(srv["name"])

    # Check slot availability
    pairs_dict = [{"service_id": p.service_id, "worker_id": p.worker_id} for p in reservation.service_worker_pairs]
    available = await get_available_slots_multi(pairs_dict, reservation.date, tid)
    slot_available = reservation.time in available.get("slots", [])

    slot_detail = available.get("slot_details", {}).get(reservation.time, {})
    if slot_detail:
        end_time = slot_detail["end_time"]
        actual_duration = slot_detail["total_duration"]
        worker_time_blocks = slot_detail.get("time_blocks", [])
    else:
        # Manually compute time blocks for force-create scenarios
        start_minutes = time_to_minutes(reservation.time)
        current_min = start_minutes
        worker_time_blocks = []
        for idx, p in enumerate(reservation.service_worker_pairs):
            srv = service_map.get(p.service_id)
            dur = srv["duration"] if srv else 0
            buf = 15 if idx > 0 else 0
            block_start = current_min + buf
            block_end = block_start + dur
            wrk = worker_map.get(p.worker_id)
            worker_time_blocks.append({
                "worker_id": p.worker_id,
                "service_id": p.service_id,
                "start_time": minutes_to_time(block_start),
                "end_time": minutes_to_time(block_end),
                "gap": buf
            })
            current_min = block_end
        end_time = minutes_to_time(current_min)
        actual_duration = current_min - start_minutes

    # Check boundary violation per worker
    boundary_violations = []
    for block in worker_time_blocks:
        wid = block.get("worker_id") if isinstance(block, dict) else block["worker_id"]
        wrk = worker_map.get(wid)
        if wrk:
            w_end = time_to_minutes(wrk.get("work_end", "21:00"))
            block_end = time_to_minutes(block["end_time"]) if isinstance(block["end_time"], str) else block["end_time"]
            if block_end > w_end:
                boundary_violations.append(
                    f"{wrk['name']} radi do {wrk.get('work_end', '21:00')}, ali usluga se završava u {block['end_time']}."
                )

    # Anti-Conflict check
    conflict_detected = False
    existing_client_reservations = await db.reservations.find({
        "client_phone": phone,
        "date": reservation.date,
        "status": {"$ne": "cancelled"},
        "tenant_id": tid,
    }).to_list(100)

    if existing_client_reservations:
        new_ranges = []
        if worker_time_blocks:
            for block in worker_time_blocks:
                new_ranges.append((time_to_minutes(block["start_time"]), time_to_minutes(block["end_time"])))
        else:
            new_ranges.append((time_to_minutes(reservation.time), time_to_minutes(end_time)))

        for existing_res in existing_client_reservations:
            existing_ranges = []
            if "worker_time_blocks" in existing_res and existing_res["worker_time_blocks"]:
                for block in existing_res["worker_time_blocks"]:
                    existing_ranges.append((time_to_minutes(block["start_time"]), time_to_minutes(block["end_time"])))
            else:
                existing_ranges.append((time_to_minutes(existing_res["time"]), time_to_minutes(existing_res["end_time"])))

            for ns, ne in new_ranges:
                for es, ee in existing_ranges:
                    if ns < ee and es < ne:
                        conflict_detected = True
                        break

    # If not force and there's an issue, return warning
    if not reservation.force:
        warnings = []
        if boundary_violations:
            warnings.extend(boundary_violations)
        elif not slot_available:
            warnings.append("Izabrani termin nije dostupan po standardnoj proveri.")
        if conflict_detected:
            warnings.append("Klijent već ima rezervaciju koja se preklapa sa ovim terminom.")
        if today_count >= 3:
            warnings.append("Klijent već ima 3 rezervacije za ovaj dan.")
        if warnings:
            raise HTTPException(status_code=409, detail="|".join(warnings))

    # Force create - proceed
    first_worker_id = worker_ids[0] if worker_ids else None
    first_worker = worker_map.get(first_worker_id, {})
    booking_id = await generate_booking_id()

    doc = {
        "booking_id": booking_id,
        "services": service_ids,
        "service_names": service_names,
        "service_worker_pairs": swp,
        "worker_time_blocks": worker_time_blocks,
        "worker_id": first_worker_id,
        "worker_name": first_worker.get("name", ""),
        "date": reservation.date,
        "time": reservation.time,
        "end_time": end_time,
        "total_duration": actual_duration,
        "total_price": total_price,
        "client_name": reservation.client_name,
        "client_phone": phone,
        "status": "confirmed",
        "payment_status": "pending_pi_payment" if PAYMENT_MODE == "PI_ECOSYSTEM" else "pending",
        "advance_required": True,
        "advance_released": False,
        "created_by": "admin",
        "tenant_id": tid,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    result = await db.reservations.insert_one(doc)

    return ReservationResponse(
        id=str(result.inserted_id),
        booking_id=booking_id,
        services=service_ids,
        service_names=service_names,
        service_worker_pairs=swp,
        worker_time_blocks=worker_time_blocks,
        worker_id=first_worker_id,
        worker_name=first_worker.get("name", ""),
        date=reservation.date,
        time=reservation.time,
        end_time=end_time,
        total_duration=actual_duration,
        total_price=total_price,
        client_name=reservation.client_name,
        client_phone=phone,
        client_email="",
        status="confirmed",
        payment_status="pending_pi_payment" if PAYMENT_MODE == "PI_ECOSYSTEM" else "pending",
        advance_required=True,
        advance_released=False,
        created_at=doc["created_at"]
    )


@api_router.get("/reservations", response_model=List[ReservationResponse])
async def get_reservations(
    request: Request,
    date: Optional[str] = None,
    worker_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    tid = await _get_tid(request)
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    await cancel_stale_unpaid_reservations(tid)

    query = {"status": {"$ne": "cancelled"}, "tenant_id": tid}
    if date:
        query["date"] = date
    if worker_id:
        query["$or"] = [
            {"worker_id": worker_id},
            {"service_worker_pairs.worker_id": worker_id},
            {"worker_time_blocks.worker_id": worker_id},
        ]

    reservations = await db.reservations.find(query).sort("date", 1).sort("time", 1).to_list(1000)

    return [
        ReservationResponse(
            id=str(r["_id"]),
            booking_id=r.get("booking_id", ""),
            services=r.get("services", []),
            service_names=r.get("service_names", []),
            service_worker_pairs=r.get("service_worker_pairs", []),
            worker_time_blocks=r.get("worker_time_blocks", []),
            worker_id=r.get("worker_id"),
            worker_name=r.get("worker_name", ""),
            date=r["date"],
            time=r["time"],
            end_time=r.get("end_time", r["time"]),
            total_duration=r.get("total_duration", 0),
            total_price=r.get("total_price", 0),
            client_name=r["client_name"],
            client_phone=r["client_phone"],
            client_email=r.get("client_email", ""),
            pi_username=r.get("pi_username", ""),
            pi_uid=r.get("pi_uid", ""),
            status=r["status"],
            payment_status=r.get("payment_status", "pending"),
            advance_required=r.get("advance_required", True),
            advance_released=r.get("advance_released", False),
            created_at=r.get("created_at", ""),
            is_rescheduled=r.get("is_rescheduled", False),
        ) for r in reservations
    ]


@api_router.put("/reservations/{reservation_id}/release-advance")
async def release_advance(reservation_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"advance_released": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Reservation not found")

    return {"message": "Advance released"}


@api_router.put("/reservations/{reservation_id}/cancel")
async def cancel_reservation(reservation_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"status": "cancelled"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Reservation not found")

    return {"message": "Reservation cancelled"}


@api_router.put("/reservations/{reservation_id}/payment-status")
async def update_payment_status(reservation_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    reservation = await db.reservations.find_one({"_id": ObjectId(reservation_id)})
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    current = reservation.get("payment_status", "pending")
    new_status = "paid" if current == "pending" else "pending"

    await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"payment_status": new_status}}
    )

    return {"payment_status": new_status}


@api_router.patch("/reservations/{reservation_id}/report-payment")
async def client_report_payment(reservation_id: str):
    """Client reports they have sent the advance payment."""
    reservation = await db.reservations.find_one({"_id": ObjectId(reservation_id), "status": {"$ne": "cancelled"}})
    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervacija nije pronađena.")

    current = reservation.get("payment_status", "pending")
    if current == "confirmed":
        raise HTTPException(status_code=400, detail="Uplata je već potvrđena.")

    await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"payment_status": "sent_for_verification"}}
    )
    return {"payment_status": "sent_for_verification"}


@api_router.patch("/admin/reservations/{reservation_id}/confirm-payment")
async def admin_confirm_payment(reservation_id: str, user: dict = Depends(get_current_user)):
    """Admin confirms the advance payment has been received."""
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    reservation = await db.reservations.find_one({"_id": ObjectId(reservation_id), "status": {"$ne": "cancelled"}})
    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervacija nije pronađena.")

    await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"payment_status": "confirmed"}}
    )
    return {"payment_status": "confirmed"}


@api_router.post("/admin/reservations/trigger-reminders")
async def trigger_reminders(request: Request, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    tid = await _get_tid(request)
    result = await process_daily_reminders(tid)
    return result


# ================== BLACKLIST ENDPOINTS ==================

@api_router.get("/blacklist")
async def get_blacklist(request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    phones = await db.blacklisted_phones.find({"tenant_id": tid}, {"_id": 0}).to_list(1000)
    return phones


@api_router.post("/blacklist")
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


@api_router.delete("/blacklist/{phone}")
async def remove_from_blacklist(phone: str, request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    phone = normalize_phone(phone)
    await db.blacklisted_phones.delete_one({"phone": phone, "tenant_id": tid})
    return {"message": "Phone removed from blacklist"}


# ================== CLIENT RESERVATIONS (by phone) ==================

@api_router.post("/my-reservations")
async def get_client_reservations(request_body: ClientReservationsRequest, request: Request):
    tid = await _get_tid(request)
    phone = normalize_phone(request_body.phone.strip())

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    reservations = await db.reservations.find({
        "client_phone": phone,
        "date": {"$gte": today},
        "status": {"$ne": "cancelled"},
        "tenant_id": tid,
    }).sort([("date", 1), ("time", 1)]).to_list(100)

    result = []
    for r in reservations:
        result.append({
            "id": str(r["_id"]),
            "services": r.get("service_names", []),
            "worker_name": r.get("worker_name", ""),
            "date": r["date"],
            "time": r["time"],
            "end_time": r.get("end_time", ""),
            "total_duration": r.get("total_duration", 0),
            "total_price": r.get("total_price", 0),
            "status": r["status"],
            "payment_status": r.get("payment_status", "pending"),
            "can_cancel": can_client_cancel(r["date"], r["time"])
        })

    return result


@api_router.put("/my-reservations/{reservation_id}/cancel")
async def client_cancel_reservation(reservation_id: str, request_body: ClientReservationsRequest, request: Request):
    tid = await _get_tid(request)
    phone = normalize_phone(request_body.phone.strip())

    reservation = await db.reservations.find_one({
        "_id": ObjectId(reservation_id),
        "client_phone": phone,
        "status": {"$ne": "cancelled"},
        "tenant_id": tid,
    })

    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervacija nije pronađena ili ne pripada ovom broju telefona.")

    if not can_client_cancel(reservation["date"], reservation["time"]):
        raise HTTPException(status_code=400, detail="Otkazivanje nije moguće manje od 24h pre termina.")

    await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"status": "cancelled", "cancelled_by": "client", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"message": "Rezervacija je uspešno otkazana."}


# ================== SETTINGS ENDPOINTS ==================

@api_router.get("/settings", response_model=SettingsResponse)
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


@api_router.put("/settings", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate, request: Request, user: dict = Depends(get_current_user)):
    tid = await _get_tid(request)
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    # Protect sensitive fields - only super_admin can modify
    PROTECTED_FIELDS = {"smtp_server", "smtp_port", "smtp_user", "smtp_password", "salon_name"}
    if user.get("role") != "super_admin":
        has_protected = PROTECTED_FIELDS & set(update_data.keys())
        if has_protected:
            raise HTTPException(status_code=403, detail="Only Super Admin can modify integration settings")
        # Also strip any protected fields that might have snuck in
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


@api_router.put("/reservations/{reservation_id}/reschedule")
async def reschedule_reservation(reservation_id: str, body: dict, request: Request, user: dict = Depends(get_current_user), background_tasks: BackgroundTasks = None):
    tid = user.get("tenant_id", "") or request.headers.get("X-Tenant-ID", "")
    new_time = body.get("new_time", "")
    new_worker_id = body.get("new_worker_id", "")
    if not new_time or not new_worker_id:
        raise HTTPException(status_code=400, detail="new_time and new_worker_id required")

    res = await db.reservations.find_one({"_id": ObjectId(reservation_id), "tenant_id": tid})
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")

    new_worker = await db.workers.find_one({"_id": ObjectId(new_worker_id), "tenant_id": tid})
    if not new_worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    old_time = res.get("time", "")
    old_worker_name = res.get("worker_name", "")
    duration = res.get("total_duration", 30)

    # Calculate new end_time
    start_min = int(new_time.split(":")[0]) * 60 + int(new_time.split(":")[1])
    end_min = start_min + duration
    new_end_time = f"{end_min // 60:02d}:{end_min % 60:02d}"

    # Update reservation
    update = {
        "time": new_time,
        "end_time": new_end_time,
        "worker_id": new_worker_id,
        "worker_name": new_worker["name"],
        "is_rescheduled": True,
    }
    # Update service_worker_pairs and worker_time_blocks
    pairs = res.get("service_worker_pairs", [])
    blocks = res.get("worker_time_blocks", [])
    if pairs:
        for p in pairs:
            p["worker_id"] = new_worker_id
            p["worker_name"] = new_worker["name"]
        update["service_worker_pairs"] = pairs
    if blocks:
        block_start = start_min
        for b in blocks:
            dur = int(b.get("end_time", "00:00").split(":")[0]) * 60 + int(b.get("end_time", "00:00").split(":")[1]) - int(b.get("start_time", "00:00").split(":")[0]) * 60 - int(b.get("start_time", "00:00").split(":")[1])
            b["worker_id"] = new_worker_id
            b["worker_name"] = new_worker["name"]
            b["start_time"] = f"{block_start // 60:02d}:{block_start % 60:02d}"
            block_start += dur + b.get("gap", 0)
            b["end_time"] = f"{(block_start - b.get('gap', 0)) // 60:02d}:{(block_start - b.get('gap', 0)) % 60:02d}"
        update["worker_time_blocks"] = blocks

    await db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": update})

    # Send email notification if client has email
    client_email = res.get("client_email", "")
    if client_email:
        settings_doc = await db.settings.find_one({"type": "salon", "tenant_id": tid})
        salon_name = settings_doc.get("salon_name", "Salon") if settings_doc else "Salon"
        background_tasks.add_task(
            send_booking_confirmation_email,
            to_email=client_email,
            salon_name=salon_name,
            booking_id=res.get("booking_id", ""),
            client_name=res.get("client_name", ""),
            date=res.get("date", ""),
            time=new_time,
            end_time=new_end_time,
            service_worker_pairs=pairs,
            total_price=res.get("total_price", 0),
            total_duration=duration,
        )

    return {
        "message": "Rescheduled",
        "old_time": old_time,
        "new_time": new_time,
        "old_worker": old_worker_name,
        "new_worker": new_worker["name"],
    }


# ================== PI PAYMENTS ==================


@api_router.post("/payments/approve")
async def approve_pi_payment(body: dict, request: Request):
    payment_id = body.get("paymentId", "")
    booking_id = body.get("booking_id", "")
    is_sandbox = body.get("is_sandbox", False)
    tid = request.headers.get("X-Tenant-ID", "")

    if not payment_id or not booking_id:
        raise HTTPException(status_code=400, detail="paymentId and booking_id required")

    if is_sandbox:
        logger.info(f"[Pi Sandbox] Approve payment {payment_id} for booking {booking_id}")
        return {"status": "approved", "message": "Sandbox auto-approved"}

    if not PI_API_KEY:
        raise HTTPException(status_code=500, detail="PI_API_KEY not configured")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{PI_API_BASE}/payments/{payment_id}/approve",
            headers={"Authorization": f"Key {PI_API_KEY}"},
        )
    if resp.status_code != 200:
        logger.error(f"[Pi] Approve failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=502, detail="Pi API approve failed")

    logger.info(f"[Pi] Approved payment {payment_id} for booking {booking_id}")
    return {"status": "approved", "pi_response": resp.json()}


@api_router.post("/payments/complete")
async def complete_pi_payment(body: dict, request: Request):
    payment_id = body.get("paymentId", "")
    txid = body.get("txid", "")
    booking_id = body.get("booking_id", "")
    is_sandbox = body.get("is_sandbox", False)
    tid = request.headers.get("X-Tenant-ID", "")

    if not payment_id or not booking_id:
        raise HTTPException(status_code=400, detail="paymentId and booking_id required")

    if is_sandbox:
        logger.info(f"[Pi Sandbox] Complete payment {payment_id} for booking {booking_id}")
        await db.reservations.update_one(
            {"booking_id": booking_id, "tenant_id": tid},
            {"$set": {"payment_status": "confirmed", "pi_payment_id": payment_id, "pi_txid": f"sandbox_{payment_id}"}}
        )
        return {"status": "completed", "message": "Sandbox payment confirmed"}

    if not PI_API_KEY:
        raise HTTPException(status_code=500, detail="PI_API_KEY not configured")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{PI_API_BASE}/payments/{payment_id}/complete",
            headers={"Authorization": f"Key {PI_API_KEY}"},
            json={"txid": txid},
        )
    if resp.status_code != 200:
        logger.error(f"[Pi] Complete failed: {resp.status_code} {resp.text}")
        raise HTTPException(status_code=502, detail="Pi API complete failed")

    await db.reservations.update_one(
        {"booking_id": booking_id, "tenant_id": tid},
        {"$set": {"payment_status": "confirmed", "pi_payment_id": payment_id, "pi_txid": txid}}
    )
    logger.info(f"[Pi] Completed payment {payment_id}, txid={txid}, booking={booking_id}")
    return {"status": "completed", "pi_response": resp.json()}


# ================== ROOT ENDPOINT ==================

@api_router.get("/")
async def root():
    return {"message": "Salon Booking API"}
