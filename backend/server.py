from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import bcrypt
import jwt
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone, timedelta

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = str(user["_id"])
        del user["_id"]
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ================== PYDANTIC MODELS ==================

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str

class ServiceCreate(BaseModel):
    name: str
    category: str  # hair, massage, nails
    duration: int  # in minutes
    price: float
    description: Optional[str] = ""

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    active: Optional[bool] = None

class ServiceResponse(BaseModel):
    id: str
    name: str
    category: str
    duration: int
    price: float
    description: str
    active: bool

class WorkerCreate(BaseModel):
    name: str
    services: List[str]  # list of service IDs they can perform
    work_start: str  # "09:00"
    work_end: str    # "21:00"
    break_start: Optional[str] = None  # "13:00"
    break_end: Optional[str] = None    # "14:00"
    days_off: List[int] = []  # 0=Sunday, 1=Monday, etc.

class WorkerUpdate(BaseModel):
    name: Optional[str] = None
    services: Optional[List[str]] = None
    work_start: Optional[str] = None
    work_end: Optional[str] = None
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    days_off: Optional[List[int]] = None
    active: Optional[bool] = None

class WorkerResponse(BaseModel):
    id: str
    name: str
    services: List[str]
    work_start: str
    work_end: str
    break_start: Optional[str]
    break_end: Optional[str]
    days_off: List[int]
    active: bool

class ServiceWorkerPair(BaseModel):
    service_id: str
    worker_id: str

class ReservationCreate(BaseModel):
    service_worker_pairs: List[ServiceWorkerPair]  # Array of {service_id, worker_id}
    date: str  # "2024-01-15"
    time: str  # "10:00"
    client_name: str
    client_phone: str

class ReservationResponse(BaseModel):
    id: str
    services: List[str]
    service_names: List[str]
    service_worker_pairs: List[dict]  # [{service_id, service_name, worker_id, worker_name}]
    worker_time_blocks: List[dict] = []  # [{worker_id, service_id, start_time, end_time}]
    date: str
    time: str
    end_time: str
    total_duration: int
    total_price: float
    client_name: str
    client_phone: str
    status: str
    advance_required: bool
    advance_released: bool
    created_at: str
    # Legacy fields for backwards compatibility
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None

class SettingsUpdate(BaseModel):
    salon_name: Optional[str] = None
    work_start: Optional[str] = None
    work_end: Optional[str] = None
    advance_instructions: Optional[str] = None

class SettingsResponse(BaseModel):
    salon_name: str
    work_start: str
    work_end: str
    advance_instructions: str

class AvailableSlotsRequest(BaseModel):
    service_worker_pairs: List[ServiceWorkerPair]  # Array of {service_id, worker_id}
    date: str

# ================== AUTH ENDPOINTS ==================

@api_router.post("/auth/login")
async def login(request: LoginRequest, response: Response):
    email = request.email.lower().strip()
    user = await db.users.find_one({"email": email})
    
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    return {
        "id": user_id,
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "access_token": access_token
    }

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

# ================== SERVICES ENDPOINTS ==================

@api_router.get("/services", response_model=List[ServiceResponse])
async def get_services(active_only: bool = True):
    query = {"active": True} if active_only else {}
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
async def create_service(service: ServiceCreate, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    doc = {
        "name": service.name,
        "category": service.category,
        "duration": service.duration,
        "price": service.price,
        "description": service.description or "",
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.services.insert_one(doc)
    return ServiceResponse(id=str(result.inserted_id), **{k: v for k, v in doc.items() if k not in ["created_at", "_id"]})

@api_router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, update: ServiceUpdate, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
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
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.services.update_one({"_id": ObjectId(service_id)}, {"$set": {"active": False}})
    return {"message": "Service deactivated"}

# ================== WORKERS ENDPOINTS ==================

@api_router.get("/workers", response_model=List[WorkerResponse])
async def get_workers(active_only: bool = True):
    query = {"active": True} if active_only else {}
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
async def create_worker(worker: WorkerCreate, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    doc = {
        "name": worker.name,
        "services": worker.services,
        "work_start": worker.work_start,
        "work_end": worker.work_end,
        "break_start": worker.break_start,
        "break_end": worker.break_end,
        "days_off": worker.days_off,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.workers.insert_one(doc)
    return WorkerResponse(id=str(result.inserted_id), **{k: v for k, v in doc.items() if k not in ["created_at", "_id"]})

@api_router.put("/workers/{worker_id}", response_model=WorkerResponse)
async def update_worker(worker_id: str, update: WorkerUpdate, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
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
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if worker exists
    worker = await db.workers.find_one({"_id": ObjectId(worker_id)})
    if not worker:
        raise HTTPException(status_code=404, detail="Radnik nije pronađen.")
    
    # Check for future reservations involving this worker
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
    
    # Hard delete
    await db.workers.delete_one({"_id": ObjectId(worker_id)})
    return {"message": "Radnik je trajno obrisan."}

# ================== RESERVATIONS ENDPOINTS ==================

def time_to_minutes(time_str: str) -> int:
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

def minutes_to_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

async def get_available_slots_multi(service_worker_pairs: List[dict], date: str) -> dict:
    """
    Get available time slots for SEQUENTIAL service/worker pairs.
    Each worker must be available for their service in sequence.
    Maximum gap allowed between services: 15 minutes.
    """
    
    if not service_worker_pairs:
        return {"slots": []}
    
    # Get service durations
    service_ids = [p["service_id"] for p in service_worker_pairs]
    service_docs = await db.services.find({"_id": {"$in": [ObjectId(s) for s in service_ids]}, "active": True}).to_list(100)
    if not service_docs:
        return {"slots": []}
    
    # Build service_id -> duration map
    service_duration = {str(s["_id"]): s["duration"] for s in service_docs}
    
    # Get unique workers
    worker_ids = list(set(p["worker_id"] for p in service_worker_pairs))
    workers = await db.workers.find({"_id": {"$in": [ObjectId(w) for w in worker_ids]}, "active": True}).to_list(100)
    worker_map = {str(w["_id"]): w for w in workers}
    
    # Parse date for day of week check
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    day_of_week = date_obj.weekday()
    day_num = (day_of_week + 1) % 7
    
    # Check all workers are working on this day
    for wid in worker_ids:
        w = worker_map.get(wid)
        if not w or day_num in w.get("days_off", []):
            return {"slots": []}
    
    # Get settings
    settings = await db.settings.find_one({"type": "salon"})
    default_start = settings.get("work_start", "09:00") if settings else "09:00"
    default_end = settings.get("work_end", "21:00") if settings else "21:00"
    
    # Get existing reservations for the date
    reservations = await db.reservations.find({
        "date": date,
        "status": {"$ne": "cancelled"}
    }).to_list(1000)
    
    # Build worker -> blocked time ranges from existing reservations
    # Now we store individual blocks per worker from worker_time_blocks
    worker_blocked = {}
    for r in reservations:
        if "worker_time_blocks" in r:
            # New format with individual worker blocks
            for block in r.get("worker_time_blocks", []):
                wid = block.get("worker_id")
                if wid:
                    start = time_to_minutes(block["start_time"])
                    end = time_to_minutes(block["end_time"])
                    if wid not in worker_blocked:
                        worker_blocked[wid] = []
                    worker_blocked[wid].append((start, end))
        elif "service_worker_pairs" in r:
            # Legacy format - block entire reservation time for all workers
            for pair in r.get("service_worker_pairs", []):
                wid = pair.get("worker_id")
                if wid:
                    start = time_to_minutes(r["time"])
                    end = time_to_minutes(r["end_time"])
                    if wid not in worker_blocked:
                        worker_blocked[wid] = []
                    worker_blocked[wid].append((start, end))
        else:
            # Very old format
            wid = r.get("worker_id")
            if wid:
                start = time_to_minutes(r["time"])
                end = time_to_minutes(r["end_time"])
                if wid not in worker_blocked:
                    worker_blocked[wid] = []
                worker_blocked[wid].append((start, end))
    
    # Find common work hours across all workers
    min_start = 0
    max_end = 24 * 60
    
    for wid in worker_ids:
        w = worker_map.get(wid)
        if w:
            work_start = time_to_minutes(w.get("work_start", default_start))
            work_end = time_to_minutes(w.get("work_end", default_end))
            min_start = max(min_start, work_start)
            max_end = min(max_end, work_end)
    
    # Calculate total duration of all services
    total_duration = sum(service_duration.get(p["service_id"], 0) for p in service_worker_pairs)
    
    # Maximum gap between services
    MAX_GAP = 15
    
    def is_worker_available(wid: str, start: int, end: int) -> bool:
        """Check if a worker is available during a time range."""
        w = worker_map.get(wid)
        if not w:
            return False
        
        # Check break time
        break_start = time_to_minutes(w["break_start"]) if w.get("break_start") else None
        break_end = time_to_minutes(w["break_end"]) if w.get("break_end") else None
        
        if break_start and break_end:
            if not (end <= break_start or start >= break_end):
                return False
        
        # Check existing reservations
        blocked = worker_blocked.get(wid, [])
        for bs, be in blocked:
            if not (end <= bs or start >= be):
                return False
        
        return True
    
    def check_sequential_availability(start_time: int) -> tuple:
        """
        Check if all services can be done sequentially starting at start_time.
        Returns (is_valid, total_end_time, time_blocks)
        """
        current_time = start_time
        time_blocks = []
        
        for idx, pair in enumerate(service_worker_pairs):
            wid = pair["worker_id"]
            duration = service_duration.get(pair["service_id"], 0)
            
            # Gap only allowed BETWEEN services (not before the first one)
            max_allowed_gap = MAX_GAP if idx > 0 else 0
            
            # Try to find a slot for this worker starting from current_time
            found = False
            for gap in range(0, max_allowed_gap + 1, 5):  # Check 0, 5, 10, 15 min gaps
                check_start = current_time + gap
                check_end = check_start + duration
                
                # Make sure we don't exceed work hours
                if check_end > max_end:
                    break
                
                if is_worker_available(wid, check_start, check_end):
                    time_blocks.append({
                        "worker_id": wid,
                        "service_id": pair["service_id"],
                        "start_time": check_start,
                        "end_time": check_end,
                        "gap": gap
                    })
                    current_time = check_end
                    found = True
                    break
            
            if not found:
                return (False, 0, [])
        
        return (True, current_time, time_blocks)
    
    # Generate slots
    slots = []
    slot_details = {}
    current = min_start
    
    while current + total_duration <= max_end:
        is_valid, end_time, time_blocks = check_sequential_availability(current)
        
        if is_valid:
            slot_time = minutes_to_time(current)
            slots.append(slot_time)
            
            # Calculate actual total duration including gaps
            actual_duration = end_time - current
            total_gap = actual_duration - total_duration
            
            slot_details[slot_time] = {
                "end_time": minutes_to_time(end_time),
                "total_duration": actual_duration,
                "service_duration": total_duration,
                "gap_minutes": total_gap,
                "time_blocks": [
                    {
                        "worker_id": b["worker_id"],
                        "service_id": b["service_id"],
                        "start_time": minutes_to_time(b["start_time"]),
                        "end_time": minutes_to_time(b["end_time"]),
                        "gap": b["gap"]
                    } for b in time_blocks
                ]
            }
        
        current += 15
    
    return {
        "slots": slots,
        "slot_details": slot_details
    }

@api_router.post("/reservations/available-slots")
async def get_slots(request: AvailableSlotsRequest):
    pairs = [{"service_id": p.service_id, "worker_id": p.worker_id} for p in request.service_worker_pairs]
    return await get_available_slots_multi(pairs, request.date)

def normalize_phone(phone: str) -> str:
    """Normalize phone number by removing all non-digit characters"""
    # Remove all non-digit characters
    normalized = ''.join(c for c in phone if c.isdigit())
    return normalized

@api_router.post("/reservations", response_model=ReservationResponse)
async def create_reservation(reservation: ReservationCreate):
    phone = normalize_phone(reservation.client_phone.strip())
    
    # Check if phone is blacklisted
    blacklisted = await db.blacklisted_phones.find_one({"phone": phone})
    if blacklisted:
        logger.info(f"Blocked phone attempted to book: {phone}")
        raise HTTPException(status_code=403, detail="Ovaj broj telefona je blokiran za rezervacije.")
    
    # Check daily limit (max 3 per phone per day)
    today_count = await db.reservations.count_documents({
        "client_phone": phone,
        "date": reservation.date,
        "status": {"$ne": "cancelled"}
    })
    logger.info(f"Phone {phone} has {today_count} reservations for date {reservation.date}")
    if today_count >= 3:
        raise HTTPException(status_code=400, detail="Maksimalno 3 rezervacije dnevno po broju telefona.")
    
    # Get all service IDs from pairs
    service_ids = [p.service_id for p in reservation.service_worker_pairs]
    worker_ids = [p.worker_id for p in reservation.service_worker_pairs]
    
    # Get services and calculate totals
    service_docs = await db.services.find({
        "_id": {"$in": [ObjectId(s) for s in service_ids]},
        "active": True
    }).to_list(100)
    
    if len(service_docs) != len(service_ids):
        raise HTTPException(status_code=400, detail="Neke izabrane usluge nisu dostupne.")
    
    service_map = {str(s["_id"]): s for s in service_docs}
    
    total_duration = sum(s["duration"] for s in service_docs)
    total_price = sum(s["price"] for s in service_docs)
    
    # Get workers
    workers = await db.workers.find({
        "_id": {"$in": [ObjectId(w) for w in worker_ids]},
        "active": True
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
    available = await get_available_slots_multi(pairs_dict, reservation.date)
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
    
    # Get first worker for legacy compatibility
    first_worker_id = worker_ids[0] if worker_ids else None
    first_worker = worker_map.get(first_worker_id, {})
    
    doc = {
        "services": service_ids,
        "service_names": service_names,
        "service_worker_pairs": service_worker_pairs,
        "worker_time_blocks": worker_time_blocks,
        "worker_id": first_worker_id,  # Legacy
        "worker_name": first_worker.get("name", ""),  # Legacy
        "date": reservation.date,
        "time": reservation.time,
        "end_time": end_time,
        "total_duration": actual_duration,
        "total_price": total_price,
        "client_name": reservation.client_name,
        "client_phone": phone,
        "status": "confirmed",
        "advance_required": True,
        "advance_released": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.reservations.insert_one(doc)
    
    return ReservationResponse(
        id=str(result.inserted_id),
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
        status="confirmed",
        advance_required=True,
        advance_released=False,
        created_at=doc["created_at"]
    )

@api_router.get("/reservations", response_model=List[ReservationResponse])
async def get_reservations(
    date: Optional[str] = None,
    worker_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {"status": {"$ne": "cancelled"}}
    if date:
        query["date"] = date
    if worker_id:
        query["worker_id"] = worker_id
    
    reservations = await db.reservations.find(query).sort("date", 1).sort("time", 1).to_list(1000)
    
    return [
        ReservationResponse(
            id=str(r["_id"]),
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
            status=r["status"],
            advance_required=r.get("advance_required", True),
            advance_released=r.get("advance_released", False),
            created_at=r.get("created_at", "")
        ) for r in reservations
    ]

@api_router.put("/reservations/{reservation_id}/release-advance")
async def release_advance(reservation_id: str, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
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
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"status": "cancelled"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    return {"message": "Reservation cancelled"}

# ================== BLACKLIST ENDPOINTS ==================

@api_router.get("/blacklist")
async def get_blacklist(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    phones = await db.blacklisted_phones.find({}, {"_id": 0}).to_list(1000)
    return phones

@api_router.post("/blacklist")
async def add_to_blacklist(phone: str, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    phone = normalize_phone(phone.strip())
    existing = await db.blacklisted_phones.find_one({"phone": phone})
    if existing:
        return {"message": "Phone already blacklisted"}
    
    await db.blacklisted_phones.insert_one({
        "phone": phone,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    logger.info(f"Phone added to blacklist: {phone}")
    return {"message": "Phone added to blacklist"}

@api_router.delete("/blacklist/{phone}")
async def remove_from_blacklist(phone: str, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    phone = normalize_phone(phone)
    
    await db.blacklisted_phones.delete_one({"phone": phone})
    return {"message": "Phone removed from blacklist"}

# ================== CLIENT RESERVATIONS (by phone) ==================

class ClientReservationsRequest(BaseModel):
    phone: str

@api_router.post("/my-reservations")
async def get_client_reservations(request: ClientReservationsRequest):
    """Get all future reservations for a phone number"""
    phone = normalize_phone(request.phone.strip())
    
    # Get current date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Find all future reservations for this phone
    reservations = await db.reservations.find({
        "client_phone": phone,
        "date": {"$gte": today},
        "status": {"$ne": "cancelled"}
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
            "can_cancel": can_client_cancel(r["date"], r["time"])
        })
    
    return result

def can_client_cancel(date_str: str, time_str: str) -> bool:
    """Check if client can cancel (at least 24h before appointment)"""
    try:
        appointment_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        appointment_dt = appointment_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours_until = (appointment_dt - now).total_seconds() / 3600
        return hours_until >= 24
    except:
        return False

@api_router.put("/my-reservations/{reservation_id}/cancel")
async def client_cancel_reservation(reservation_id: str, request: ClientReservationsRequest):
    """Client cancels their own reservation (must be 24h+ before)"""
    phone = normalize_phone(request.phone.strip())
    
    # Find reservation
    reservation = await db.reservations.find_one({
        "_id": ObjectId(reservation_id),
        "client_phone": phone,
        "status": {"$ne": "cancelled"}
    })
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Rezervacija nije pronađena ili ne pripada ovom broju telefona.")
    
    # Check if can cancel (24h rule)
    if not can_client_cancel(reservation["date"], reservation["time"]):
        raise HTTPException(status_code=400, detail="Otkazivanje nije moguće manje od 24h pre termina.")
    
    # Cancel reservation
    await db.reservations.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"status": "cancelled", "cancelled_by": "client", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Rezervacija je uspešno otkazana."}

# ================== SETTINGS ENDPOINTS ==================

@api_router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    settings = await db.settings.find_one({"type": "salon"})
    if not settings:
        return SettingsResponse(
            salon_name="Beauty Salon",
            work_start="09:00",
            work_end="21:00",
            advance_instructions="Uplata avansa je obavezna 24h pre termina. Instrukcije za uplatu će vam biti poslate."
        )
    return SettingsResponse(
        salon_name=settings.get("salon_name", "Beauty Salon"),
        work_start=settings.get("work_start", "09:00"),
        work_end=settings.get("work_end", "21:00"),
        advance_instructions=settings.get("advance_instructions", "")
    )

@api_router.put("/settings", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data["type"] = "salon"
    
    await db.settings.update_one(
        {"type": "salon"},
        {"$set": update_data},
        upsert=True
    )
    
    settings = await db.settings.find_one({"type": "salon"})
    return SettingsResponse(
        salon_name=settings.get("salon_name", "Beauty Salon"),
        work_start=settings.get("work_start", "09:00"),
        work_end=settings.get("work_end", "21:00"),
        advance_instructions=settings.get("advance_instructions", "")
    )

# ================== ROOT ENDPOINT ==================

@api_router.get("/")
async def root():
    return {"message": "Salon Booking API"}

# Include the router in the main app
app.include_router(api_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000"), "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup event - seed admin and create indexes
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
    
    # Clean up duplicates and seed initial data
    # Only seed if no ACTIVE workers exist
    existing_services = await db.services.count_documents({"active": True})
    existing_workers = await db.workers.count_documents({"active": True})
    
    # Only clean up if there are more than 5 services or more than 3 workers (duplicates)
    total_services = await db.services.count_documents({})
    total_workers = await db.workers.count_documents({})
    
    if total_services > 10 or total_workers > 5:
        # Clear duplicates detected
        logger.info("Cleaning up duplicate services and workers...")
        await db.services.delete_many({})
        await db.workers.delete_many({})
        existing_services = 0
        existing_workers = 0
    
    # Seed services if no active ones exist
    if existing_services == 0:
        logger.info("Seeding initial services...")
        default_services = [
            {
                "name": "Šišanje",
                "category": "hair",
                "duration": 30,
                "price": 2000.0,
                "description": "Klasično šišanje",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "name": "Farbanje kose",
                "category": "hair",
                "duration": 90,
                "price": 5000.0,
                "description": "Farbanje cele kose",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "name": "Manikir",
                "category": "nails",
                "duration": 45,
                "price": 2500.0,
                "description": "Klasični manikir",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "name": "Pedikir",
                "category": "nails",
                "duration": 60,
                "price": 3000.0,
                "description": "Klasični pedikir",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "name": "Relax masaža",
                "category": "massage",
                "duration": 60,
                "price": 4000.0,
                "description": "Opuštajuća masaža celog tela",
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        result = await db.services.insert_many(default_services)
        service_ids = [str(sid) for sid in result.inserted_ids]
        logger.info(f"Created {len(service_ids)} services")
    else:
        # Get existing service IDs
        services = await db.services.find({"active": True}).to_list(100)
        service_ids = [str(s["_id"]) for s in services]
    
    # Seed worker if none exist
    if existing_workers == 0:
        logger.info("Seeding initial worker...")
        await db.workers.insert_one({
            "name": "Ana",
            "services": service_ids,  # Ana can do ALL services
            "work_start": "09:00",
            "work_end": "21:00",
            "break_start": "13:00",
            "break_end": "14:00",
            "days_off": [0],  # Sunday off
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info("Created worker: Ana")
    
    # Write test credentials
    import os as os_module
    os_module.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write(f"# Test Credentials\n\n")
        f.write(f"## Admin\n")
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
