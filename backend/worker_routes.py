"""
Worker routes: CRUD + account management.
"""
import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from bson import ObjectId
from typing import List
from datetime import datetime, timezone

from database import db
from models import WorkerCreate, WorkerUpdate, WorkerResponse, WorkerAccountCreate
from auth import hash_password, get_current_user
from tenant import check_tenant_access
from route_utils import _get_tid, _generate_temp_password

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/workers", response_model=List[WorkerResponse])
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


@router.get("/workers/account-statuses")
async def get_worker_account_statuses(request: Request, user: dict = Depends(get_current_user)):
    """Bulk fetch account status for all workers in a tenant. Single DB query."""
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    tid = await _get_tid(request)
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    accounts = await db.users.find(
        {"tenant_id": tid, "role": "worker", "worker_id": {"$exists": True, "$ne": ""}},
        {"worker_id": 1, "email": 1, "created_at": 1, "_id": 0}
    ).to_list(200)

    result = {}
    for acc in accounts:
        result[acc["worker_id"]] = {
            "has_account": True,
            "email": acc["email"],
            "created_at": acc.get("created_at", ""),
        }

    return result


@router.post("/workers", response_model=WorkerResponse)
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


@router.put("/workers/{worker_id}", response_model=WorkerResponse)
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


@router.delete("/workers/{worker_id}")
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


@router.post("/workers/{worker_id}/create-account")
async def create_worker_account(worker_id: str, body: WorkerAccountCreate, request: Request, user: dict = Depends(get_current_user)):
    """Admin creates a login account for a worker. Auto-generates a temporary password."""
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    tid = await _get_tid(request)
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    # Verify worker exists
    worker = await db.workers.find_one({"_id": ObjectId(worker_id), "tenant_id": tid})
    if not worker:
        raise HTTPException(status_code=404, detail="Radnik nije pronađen.")

    email = body.email.lower().strip()

    # Check if email already taken
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=409, detail="Email je već u upotrebi.")

    # Check if worker already has an account
    existing_account = await db.users.find_one({"worker_id": worker_id, "tenant_id": tid})
    if existing_account:
        raise HTTPException(status_code=409, detail="Radnik već ima nalog.")

    temp_password = _generate_temp_password()

    await db.users.insert_one({
        "email": email,
        "password_hash": hash_password(temp_password),
        "name": worker["name"],
        "role": "worker",
        "worker_id": worker_id,
        "tenant_id": tid,
        "language_preference": body.language_preference,
        "must_change_password": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    logger.info(f"Worker account created: {email} for worker {worker['name']} ({worker_id})")

    return {
        "message": f"Nalog kreiran za {worker['name']}",
        "email": email,
        "temp_password": temp_password,
        "worker_id": worker_id,
        "worker_name": worker["name"],
    }


@router.delete("/workers/{worker_id}/account")
async def delete_worker_account(worker_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Admin deletes a worker's login account."""
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    tid = await _get_tid(request)
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    result = await db.users.delete_one({"worker_id": worker_id, "tenant_id": tid, "role": "worker"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nalog radnika nije pronađen.")

    return {"message": "Nalog radnika je obrisan."}


@router.get("/workers/{worker_id}/account")
async def get_worker_account(worker_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Check if a worker has a login account."""
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    tid = await _get_tid(request)
    account = await db.users.find_one({"worker_id": worker_id, "tenant_id": tid, "role": "worker"})
    if not account:
        return {"has_account": False}

    return {
        "has_account": True,
        "email": account["email"],
        "created_at": account.get("created_at", ""),
    }


@router.put("/workers/{worker_id}/reset-password")
async def reset_worker_password(worker_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Admin resets a worker's password to a new temporary one."""
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    tid = await _get_tid(request)
    if user.get("role") != "super_admin":
        check_tenant_access(user, tid)

    account = await db.users.find_one({"worker_id": worker_id, "tenant_id": tid, "role": "worker"})
    if not account:
        raise HTTPException(status_code=404, detail="Nalog radnika nije pronađen.")

    temp_password = _generate_temp_password()

    await db.users.update_one(
        {"_id": account["_id"]},
        {"$set": {
            "password_hash": hash_password(temp_password),
            "must_change_password": True,
        }}
    )

    logger.info(f"Worker password reset: {account['email']} ({worker_id})")

    return {
        "message": f"Lozinka resetovana za {account.get('name', '')}",
        "email": account["email"],
        "temp_password": temp_password,
        "worker_name": account.get("name", ""),
    }
