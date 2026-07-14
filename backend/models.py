from pydantic import BaseModel
from typing import List, Optional


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
    category: str
    duration: int
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
    services: List[str]
    work_start: str
    work_end: str
    break_start: Optional[str] = None
    break_end: Optional[str] = None
    days_off: List[int] = []

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
    service_worker_pairs: List[ServiceWorkerPair]
    date: str
    time: str
    client_name: str
    client_phone: str
    client_email: str = ""
    pi_username: Optional[str] = None
    pi_uid: Optional[str] = None

class ReservationResponse(BaseModel):
    id: str
    booking_id: str = ""
    services: List[str]
    service_names: List[str]
    service_worker_pairs: List[dict]
    worker_time_blocks: List[dict] = []
    date: str
    time: str
    end_time: str
    total_duration: int
    total_price: float
    client_name: str
    client_phone: str
    status: str
    payment_status: str = "pending"
    advance_required: bool
    advance_released: bool
    created_at: str
    client_email: str = ""
    pi_username: Optional[str] = None
    pi_uid: Optional[str] = None
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None

class SettingsUpdate(BaseModel):
    salon_name: Optional[str] = None
    work_start: Optional[str] = None
    work_end: Optional[str] = None
    advance_instructions: Optional[str] = None
    pi_wallet_address: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None

class SettingsResponse(BaseModel):
    salon_name: str
    work_start: str
    work_end: str
    advance_instructions: str
    pi_wallet_address: str = ""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

class AvailableSlotsRequest(BaseModel):
    service_worker_pairs: List[ServiceWorkerPair]
    date: str

class CategoryToggle(BaseModel):
    category: str
    enabled: bool

class AdminReservationCreate(BaseModel):
    service_worker_pairs: List[ServiceWorkerPair]
    date: str
    time: str
    client_name: str
    client_phone: str
    force: bool = False

class ClientReservationsRequest(BaseModel):
    phone: str
