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

class ReservationCreate(BaseModel):
    services: List[str]  # service IDs
    worker_id: Optional[str] = None  # None = "Anyone"
    date: str  # "2024-01-15"
    time: str  # "10:00"
    client_name: str
    client_phone: str

class ReservationResponse(BaseModel):
    id: str
    services: List[str]
    service_names: List[str]
    worker_id: str
    worker_name: str
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
    services: List[str]
    worker_id: Optional[str] = None
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
    
    await db.workers.update_one({"_id": ObjectId(worker_id)}, {"$set": {"active": False}})
    return {"message": "Worker deactivated"}

# ================== RESERVATIONS ENDPOINTS ==================

def time_to_minutes(time_str: str) -> int:
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

def minutes_to_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

async def get_available_slots(services: List[str], worker_id: Optional[str], date: str) -> dict:
    """Get available time slots for given services and optional worker on a date."""
    
    # Calculate total duration
    service_docs = await db.services.find({"_id": {"$in": [ObjectId(s) for s in services]}, "active": True}).to_list(100)
    if not service_docs:
        return {"slots": [], "workers": {}}
    
    total_duration = sum(s["duration"] for s in service_docs)
    service_ids_set = set(services)
    
    # Get workers that can perform ALL selected services
    all_workers = await db.workers.find({"active": True}).to_list(100)
    
    # Parse date for day of week check
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
    # Convert to our format: 0=Sunday, 1=Monday, etc.
    day_num = (day_of_week + 1) % 7
    
    eligible_workers = []
    for w in all_workers:
        worker_services = set(w.get("services", []))
        if service_ids_set.issubset(worker_services) and day_num not in w.get("days_off", []):
            if worker_id is None or str(w["_id"]) == worker_id:
                eligible_workers.append(w)
    
    if not eligible_workers:
        return {"slots": [], "workers": {}}
    
    # Get settings for work hours
    settings = await db.settings.find_one({"type": "salon"})
    default_start = settings.get("work_start", "09:00") if settings else "09:00"
    default_end = settings.get("work_end", "21:00") if settings else "21:00"
    
    # Get existing reservations for the date
    reservations = await db.reservations.find({
        "date": date,
        "status": {"$ne": "cancelled"}
    }).to_list(1000)
    
    # Build worker -> blocked time ranges
    worker_blocked = {}
    for r in reservations:
        wid = r["worker_id"]
        start = time_to_minutes(r["time"])
        end = time_to_minutes(r["end_time"])
        if wid not in worker_blocked:
            worker_blocked[wid] = []
        worker_blocked[wid].append((start, end))
    
    # Calculate available slots per worker
    result = {"slots": set(), "workers": {}}
    
    for w in eligible_workers:
        wid = str(w["_id"])
        work_start = time_to_minutes(w.get("work_start", default_start))
        work_end = time_to_minutes(w.get("work_end", default_end))
        break_start = time_to_minutes(w["break_start"]) if w.get("break_start") else None
        break_end = time_to_minutes(w["break_end"]) if w.get("break_end") else None
        
        blocked = worker_blocked.get(wid, [])
        
        # Generate 15-minute slots
        current = work_start
        worker_slots = []
        
        while current + total_duration <= work_end:
            slot_end = current + total_duration
            
            # Check if slot overlaps with break
            if break_start and break_end:
                if not (slot_end <= break_start or current >= break_end):
                    current += 15
                    continue
            
            # Check if slot overlaps with existing reservations
            overlap = False
            for bs, be in blocked:
                if not (slot_end <= bs or current >= be):
                    overlap = True
                    break
            
            if not overlap:
                slot_time = minutes_to_time(current)
                result["slots"].add(slot_time)
                worker_slots.append(slot_time)
            
            current += 15
        
        if worker_slots:
            result["workers"][wid] = {
                "name": w["name"],
                "slots": worker_slots
            }
    
    result["slots"] = sorted(list(result["slots"]))
    return result

@api_router.post("/reservations/available-slots")
async def get_slots(request: AvailableSlotsRequest):
    return await get_available_slots(request.services, request.worker_id, request.date)

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
    
    # Get services and calculate totals
    service_docs = await db.services.find({
        "_id": {"$in": [ObjectId(s) for s in reservation.services]},
        "active": True
    }).to_list(100)
    
    if not service_docs:
        raise HTTPException(status_code=400, detail="Izabrane usluge nisu dostupne.")
    
    total_duration = sum(s["duration"] for s in service_docs)
    total_price = sum(s["price"] for s in service_docs)
    service_names = [s["name"] for s in service_docs]
    
    # Determine worker
    worker_id = reservation.worker_id
    if not worker_id:
        # "Anyone" - find an available worker
        available = await get_available_slots(reservation.services, None, reservation.date)
        for wid, wdata in available.get("workers", {}).items():
            if reservation.time in wdata.get("slots", []):
                worker_id = wid
                break
    
    if not worker_id:
        raise HTTPException(status_code=400, detail="Nema dostupnih radnika za izabrani termin.")
    
    # Verify slot is still available
    available = await get_available_slots(reservation.services, worker_id, reservation.date)
    if reservation.time not in available.get("slots", []):
        raise HTTPException(status_code=400, detail="Izabrani termin više nije dostupan.")
    
    # Get worker name
    worker = await db.workers.find_one({"_id": ObjectId(worker_id)})
    worker_name = worker["name"] if worker else "Unknown"
    
    # Calculate end time
    start_minutes = time_to_minutes(reservation.time)
    end_time = minutes_to_time(start_minutes + total_duration)
    
    doc = {
        "services": reservation.services,
        "service_names": service_names,
        "worker_id": worker_id,
        "worker_name": worker_name,
        "date": reservation.date,
        "time": reservation.time,
        "end_time": end_time,
        "total_duration": total_duration,
        "total_price": total_price,
        "client_name": reservation.client_name,
        "client_phone": phone,
        "status": "confirmed",
        "advance_required": True,
        "advance_released": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.reservations.insert_one(doc)
    
    return ReservationResponse(id=str(result.inserted_id), **{k: v for k, v in doc.items() if k != "_id"})

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
            services=r["services"],
            service_names=r.get("service_names", []),
            worker_id=r["worker_id"],
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
