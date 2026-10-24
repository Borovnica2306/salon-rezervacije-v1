"""
Booking routes: reservations CRUD, client-facing, available slots, reschedule, Pi payments.
"""
import logging
import httpx
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from bson import ObjectId
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from database import db
from models import (
    ReservationCreate, ReservationResponse, AvailableSlotsRequest,
    ClientReservationsRequest, AdminReservationCreate,
)
from auth import get_current_user
from logic import (
    time_to_minutes, minutes_to_time, normalize_phone,
    generate_booking_id, can_client_cancel,
    get_available_slots_multi, cancel_stale_unpaid_reservations,
)
from mail_service import send_booking_confirmation_email, PAYMENT_MODE
from tenant import check_tenant_access
from route_utils import _get_tid, _get_salon_today, PI_API_KEY, PI_API_BASE, COUNTRY_TIMEZONES
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

router = APIRouter()


# ================== RESERVATIONS ENDPOINTS ==================

@router.post("/reservations/available-slots")
async def get_slots(request_body: AvailableSlotsRequest, request: Request):
    tid = await _get_tid(request)
    await cancel_stale_unpaid_reservations(tid)
    pairs = [{"service_id": p.service_id, "worker_id": p.worker_id} for p in request_body.service_worker_pairs]
    return await get_available_slots_multi(pairs, request_body.date, tid)


@router.post("/reservations", response_model=ReservationResponse)
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
        "lang": reservation.lang or "sr",
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
            lang=reservation.lang or "sr",
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


@router.post("/admin/reservations", response_model=ReservationResponse)
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

    today_count = await db.reservations.count_documents({
        "client_phone": phone,
        "date": reservation.date,
        "status": {"$ne": "cancelled"},
        "tenant_id": tid,
    })

    service_ids = [p.service_id for p in reservation.service_worker_pairs]
    worker_ids = [p.worker_id for p in reservation.service_worker_pairs]

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

    workers_list = await db.workers.find({
        "_id": {"$in": [ObjectId(w) for w in worker_ids]},
        "active": True,
        "tenant_id": tid,
    }).to_list(100)

    if len(workers_list) != len(set(worker_ids)):
        raise HTTPException(status_code=400, detail="Neki izabrani radnici nisu dostupni.")

    worker_map = {str(w["_id"]): w for w in workers_list}

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

    pairs_dict = [{"service_id": p.service_id, "worker_id": p.worker_id} for p in reservation.service_worker_pairs]
    available = await get_available_slots_multi(pairs_dict, reservation.date, tid)
    slot_available = reservation.time in available.get("slots", [])

    slot_detail = available.get("slot_details", {}).get(reservation.time, {})
    if slot_detail:
        end_time = slot_detail["end_time"]
        actual_duration = slot_detail["total_duration"]
        worker_time_blocks = slot_detail.get("time_blocks", [])
    else:
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


@router.get("/reservations", response_model=List[ReservationResponse])
async def get_reservations(
    request: Request,
    date: Optional[str] = None,
    worker_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    if user.get("role") not in ("admin", "super_admin", "worker"):
        raise HTTPException(status_code=403, detail="Access required")

    tid = await _get_tid(request)
    if user.get("role") not in ("super_admin",):
        check_tenant_access(user, tid)

    await cancel_stale_unpaid_reservations(tid)

    query = {"status": {"$ne": "cancelled"}, "tenant_id": tid}

    is_worker = user.get("role") == "worker"

    if is_worker:
        user_worker_id = user.get("worker_id", "")
        if not user_worker_id:
            raise HTTPException(status_code=403, detail="Worker account not linked")

        salon_today = await _get_salon_today(tid)
        salon_end = (datetime.strptime(salon_today, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")

        query["date"] = {"$gte": salon_today, "$lte": salon_end}
        query["$or"] = [
            {"worker_id": user_worker_id},
            {"service_worker_pairs.worker_id": user_worker_id},
            {"worker_time_blocks.worker_id": user_worker_id},
        ]
    else:
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


@router.put("/reservations/{reservation_id}/release-advance")
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


@router.put("/reservations/{reservation_id}/cancel")
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


@router.put("/reservations/{reservation_id}/payment-status")
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


@router.patch("/reservations/{reservation_id}/report-payment")
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


@router.patch("/admin/reservations/{reservation_id}/confirm-payment")
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


# ================== CLIENT RESERVATIONS (by phone) ==================

@router.post("/my-reservations")
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


@router.put("/my-reservations/{reservation_id}/cancel")
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


# ================== RESCHEDULE ==================

def _ttm(t: str) -> int:
    """Time string 'HH:MM' to minutes."""
    h, m = t.split(":")
    return int(h) * 60 + int(m)

def _mtt(m: int) -> str:
    """Minutes to 'HH:MM' string."""
    return f"{m // 60:02d}:{m % 60:02d}"


@router.put("/reservations/{reservation_id}/reschedule")
async def reschedule_reservation(reservation_id: str, body: dict, request: Request, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    if user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    tid = user.get("tenant_id", "") or request.headers.get("X-Tenant-ID", "")
    new_time = body.get("new_time", "")
    new_worker_id = body.get("new_worker_id", "")
    block_index = body.get("block_index")  # Which block was dragged (None = single-service)
    new_date = body.get("new_date", "")

    if not new_time or not new_worker_id:
        raise HTTPException(status_code=400, detail="new_time and new_worker_id required")

    if not ObjectId.is_valid(reservation_id) or not ObjectId.is_valid(new_worker_id):
        raise HTTPException(status_code=400, detail="Neispravan ID")

    res = await db.reservations.find_one({"_id": ObjectId(reservation_id), "tenant_id": tid})
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if res.get("status") == "cancelled":
        raise HTTPException(status_code=400, detail="Otkazana rezervacija se ne može premestiti.")

    new_worker = await db.workers.find_one({"_id": ObjectId(new_worker_id), "tenant_id": tid})
    if not new_worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    old_time = res.get("time", "")
    old_worker_name = res.get("worker_name", "")
    blocks = res.get("worker_time_blocks", [])
    pairs = res.get("service_worker_pairs", [])
    old_date = res["date"]
    date = new_date or old_date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Neispravan datum")

    # Zabrana premeštanja u prošlost (po vremenskoj zoni salona)
    tenant = await db.tenants.find_one({"tenant_id": tid}, {"country": 1})
    tz_name = COUNTRY_TIMEZONES.get((tenant or {}).get("country", "RS"), "Europe/Belgrade")
    salon_now = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M")
    if old_date < salon_now[:10]:
        raise HTTPException(status_code=400, detail="Nije moguće premestiti rezervaciju iz prošlog dana.")
    if f"{date} {new_time}" < salon_now:
        raise HTTPException(status_code=400, detail="Nije moguće premestiti rezervaciju u prošlost.")

    # ===== MULTI-SERVICE PACKAGE RESCHEDULE =====
    if blocks and len(blocks) > 1:
        # Determine which block was dragged
        dragged_idx = block_index if block_index is not None and 0 <= block_index < len(blocks) else 0
        dragged_block = blocks[dragged_idx]

        # Calculate time delta
        old_dragged_start = _ttm(dragged_block["start_time"])
        new_dragged_start = _ttm(new_time)
        delta = new_dragged_start - old_dragged_start

        # Shift ALL blocks by delta; only dragged block gets new worker
        new_blocks = []
        for i, b in enumerate(blocks):
            old_start = _ttm(b["start_time"])
            old_end = _ttm(b["end_time"])
            shifted_start = old_start + delta
            shifted_end = old_end + delta

            nb = {**b}
            nb["start_time"] = _mtt(shifted_start)
            nb["end_time"] = _mtt(shifted_end)

            if i == dragged_idx:
                nb["worker_id"] = new_worker_id
                if pairs and i < len(pairs):
                    pairs[i]["worker_id"] = new_worker_id
                    pairs[i]["worker_name"] = new_worker["name"]

            new_blocks.append(nb)

        # Overall reservation time range
        package_start = min(_ttm(b["start_time"]) for b in new_blocks)
        package_end = max(_ttm(b["end_time"]) for b in new_blocks)

        # ===== OVERLAP CHECK FOR EVERY WORKER IN THE PACKAGE =====
        checked_workers = {}
        for b in new_blocks:
            wid = b["worker_id"]
            b_start = b["start_time"]
            b_end = b["end_time"]

            # Fetch worker name for error messages
            if wid not in checked_workers:
                w = await db.workers.find_one({"_id": ObjectId(wid)}, {"name": 1})
                checked_workers[wid] = w["name"] if w else wid

            overlap = await db.reservations.find_one({
                "_id": {"$ne": ObjectId(reservation_id)},
                "tenant_id": tid,
                "date": date,
                "status": {"$ne": "cancelled"},
                "$or": [
                    {"worker_id": wid},
                    {"service_worker_pairs.worker_id": wid},
                    {"worker_time_blocks.worker_id": wid},
                ],
                "time": {"$lt": b_end},
                "end_time": {"$gt": b_start},
            })
            if overlap:
                svc_name = ""
                if pairs and new_blocks.index(b) < len(pairs):
                    svc_name = pairs[new_blocks.index(b)].get("service_name", "")
                raise HTTPException(
                    status_code=400,
                    detail=f"Radnik {checked_workers[wid]} je zauzet u {b_start}-{b_end}" +
                           (f" (usluga: {svc_name})" if svc_name else "") +
                           ". Ceo paket nije moguće premestiti."
                )

        # Client overlap check for the full package time range
        client_phone = res.get("client_phone", "")
        if client_phone:
            client_overlap = await db.reservations.find_one({
                "_id": {"$ne": ObjectId(reservation_id)},
                "tenant_id": tid,
                "date": date,
                "status": {"$ne": "cancelled"},
                "client_phone": client_phone,
                "time": {"$lt": _mtt(package_end)},
                "end_time": {"$gt": _mtt(package_start)},
            })
            if client_overlap:
                raise HTTPException(
                    status_code=400,
                    detail="Klijent već ima zakazan termin koji se preklapa sa ovim vremenom."
                )

        # All checks passed — update
        update = {
            "time": _mtt(package_start),
            "end_time": _mtt(package_end),
            "worker_time_blocks": new_blocks,
            "service_worker_pairs": pairs,
            "is_rescheduled": True,
            "date": date,
        }
        # Update primary worker_id to the first block's worker
        update["worker_id"] = new_blocks[0]["worker_id"]
        w0 = await db.workers.find_one({"_id": ObjectId(new_blocks[0]["worker_id"])}, {"name": 1})
        update["worker_name"] = w0["name"] if w0 else ""

        new_end_time = _mtt(package_end)
        new_start_time = _mtt(package_start)

    else:
        # ===== SINGLE-SERVICE RESCHEDULE (original logic) =====
        duration = res.get("total_duration", 30)
        start_min = _ttm(new_time)
        end_min = start_min + duration
        new_end_time = _mtt(end_min)
        new_start_time = new_time

        # Worker overlap
        overlap = await db.reservations.find_one({
            "_id": {"$ne": ObjectId(reservation_id)},
            "tenant_id": tid,
            "date": date,
            "status": {"$ne": "cancelled"},
            "$or": [
                {"worker_id": new_worker_id},
                {"service_worker_pairs.worker_id": new_worker_id},
            ],
            "time": {"$lt": new_end_time},
            "end_time": {"$gt": new_time},
        })
        if overlap:
            raise HTTPException(status_code=400, detail="Termin je zauzet")

        # Client overlap
        client_phone = res.get("client_phone", "")
        if client_phone:
            client_overlap = await db.reservations.find_one({
                "_id": {"$ne": ObjectId(reservation_id)},
                "tenant_id": tid,
                "date": date,
                "status": {"$ne": "cancelled"},
                "client_phone": client_phone,
                "time": {"$lt": new_end_time},
                "end_time": {"$gt": new_time},
            })
            if client_overlap:
                raise HTTPException(
                    status_code=400,
                    detail="Klijent već ima zakazan termin koji se preklapa sa ovim vremenom."
                )

        update = {
            "time": new_time,
            "end_time": new_end_time,
            "worker_id": new_worker_id,
            "worker_name": new_worker["name"],
            "is_rescheduled": True,
            "date": date,
        }
        if pairs:
            for p in pairs:
                p["worker_id"] = new_worker_id
                p["worker_name"] = new_worker["name"]
            update["service_worker_pairs"] = pairs
        if blocks and len(blocks) == 1:
            blocks[0]["worker_id"] = new_worker_id
            blocks[0]["start_time"] = new_time
            blocks[0]["end_time"] = new_end_time
            update["worker_time_blocks"] = blocks

    await db.reservations.update_one({"_id": ObjectId(reservation_id)}, {"$set": update})

    # Send email notification
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
            date=date,
            time=new_start_time,
            end_time=new_end_time,
            service_worker_pairs=pairs,
            total_price=res.get("total_price", 0),
            total_duration=res.get("total_duration", 30),
            lang=res.get("lang", "sr"),
        )

    return {
        "message": "Rescheduled",
        "old_time": old_time,
        "new_time": new_start_time,
        "old_worker": old_worker_name,
        "new_worker": new_worker["name"],
        "new_date": date,
    }


# ================== PI PAYMENTS ==================

@router.post("/payments/approve")
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


@router.post("/payments/complete")
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
