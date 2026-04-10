import string
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import List
from bson import ObjectId
from database import db, MASTER_CATEGORIES

logger = logging.getLogger(__name__)

# ================== TIME UTILITIES ==================

def time_to_minutes(time_str: str) -> int:
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


def minutes_to_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def normalize_phone(phone: str) -> str:
    digits = ''.join(c for c in phone if c.isdigit())
    # Strip leading country code prefix to get local number
    if digits.startswith('381'):
        digits = digits[3:]
    # Strip leading zero
    if digits.startswith('0'):
        digits = digits[1:]
    # Return in consistent format: 381 + local number
    return '381' + digits


async def generate_booking_id() -> str:
    chars = string.ascii_uppercase + string.digits
    for _ in range(20):
        bid = ''.join(random.choices(chars, k=4))
        exists = await db.reservations.find_one({"booking_id": bid})
        if not exists:
            return bid
    return ''.join(random.choices(chars, k=6))


async def get_enabled_categories() -> List[str]:
    configs = await db.categories_config.find().to_list(100)
    if not configs:
        return list(MASTER_CATEGORIES.keys())
    return [c["category"] for c in configs if c.get("enabled", True)]


def can_client_cancel(date_str: str, time_str: str) -> bool:
    try:
        appointment_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        appointment_dt = appointment_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours_until = (appointment_dt - now).total_seconds() / 3600
        return hours_until >= 24
    except Exception:
        return False


# ================== SMART PAIRING LOGIC ==================

# Fixed Social Buffer between consecutive services (exactly 15 minutes)
SOCIAL_BUFFER = 15


async def get_available_slots_multi(service_worker_pairs: List[dict], date: str) -> dict:
    """
    Get available time slots for SEQUENTIAL service/worker pairs.
    Each worker must be available for their service in sequence.
    Fixed 15-minute Social Buffer between consecutive services.
    All-or-Nothing: entire chain must be valid.
    """

    if not service_worker_pairs:
        return {"slots": []}

    # Get service durations
    service_ids = [p["service_id"] for p in service_worker_pairs]
    service_docs = await db.services.find({"_id": {"$in": [ObjectId(s) for s in service_ids]}, "active": True}).to_list(100)
    if not service_docs:
        return {"slots": []}

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
    worker_blocked = {}
    for r in reservations:
        if "worker_time_blocks" in r:
            for block in r.get("worker_time_blocks", []):
                wid = block.get("worker_id")
                if wid:
                    start = time_to_minutes(block["start_time"])
                    end = time_to_minutes(block["end_time"])
                    if wid not in worker_blocked:
                        worker_blocked[wid] = []
                    worker_blocked[wid].append((start, end))
        elif "service_worker_pairs" in r:
            for pair in r.get("service_worker_pairs", []):
                wid = pair.get("worker_id")
                if wid:
                    start = time_to_minutes(r["time"])
                    end = time_to_minutes(r["end_time"])
                    if wid not in worker_blocked:
                        worker_blocked[wid] = []
                    worker_blocked[wid].append((start, end))
        else:
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

    # Total chain duration = service durations + buffers between them
    num_buffers = max(0, len(service_worker_pairs) - 1)
    total_chain_duration = total_duration + (num_buffers * SOCIAL_BUFFER)

    def is_worker_available(wid: str, start: int, end: int) -> bool:
        w = worker_map.get(wid)
        if not w:
            return False

        break_start = time_to_minutes(w["break_start"]) if w.get("break_start") else None
        break_end = time_to_minutes(w["break_end"]) if w.get("break_end") else None

        if break_start and break_end:
            if not (end <= break_start or start >= break_end):
                return False

        blocked = worker_blocked.get(wid, [])
        for bs, be in blocked:
            if not (end <= bs or start >= be):
                return False

        return True

    def check_sequential_availability(start_time: int) -> tuple:
        """
        Check if all services can be done sequentially starting at start_time.
        Fixed 15-minute Social Buffer between consecutive services.
        All-or-Nothing: entire chain must be valid or the slot is rejected.
        Returns (is_valid, total_end_time, time_blocks)
        """
        current_time = start_time
        time_blocks = []

        for idx, pair in enumerate(service_worker_pairs):
            wid = pair["worker_id"]
            duration = service_duration.get(pair["service_id"], 0)

            # Fixed 15-min Social Buffer BETWEEN services (not before first)
            buffer = SOCIAL_BUFFER if idx > 0 else 0
            check_start = current_time + buffer
            check_end = check_start + duration

            # Service must finish within work hours
            if check_end > max_end:
                return (False, 0, [])

            # Worker must be available for this exact time block
            if not is_worker_available(wid, check_start, check_end):
                return (False, 0, [])

            time_blocks.append({
                "worker_id": wid,
                "service_id": pair["service_id"],
                "start_time": check_start,
                "end_time": check_end,
                "gap": buffer
            })
            current_time = check_end

        return (True, current_time, time_blocks)

    # Generate slots
    slots = []
    slot_details = {}
    current = min_start

    while current + total_chain_duration <= max_end:
        is_valid, end_time, time_blocks = check_sequential_availability(current)

        if is_valid:
            slot_time = minutes_to_time(current)
            slots.append(slot_time)

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

    # Filter out slots that start within 2 hours for today (Belgrade time)
    belgrade_tz = timezone(timedelta(hours=2))
    now_belgrade = datetime.now(belgrade_tz)
    today_belgrade = now_belgrade.strftime("%Y-%m-%d")
    if date == today_belgrade:
        now_minutes = now_belgrade.hour * 60 + now_belgrade.minute
        min_allowed = now_minutes + 120
        slots = [s for s in slots if time_to_minutes(s) >= min_allowed]
        slot_details = {k: v for k, v in slot_details.items() if time_to_minutes(k) >= min_allowed}

    return {
        "slots": slots,
        "slot_details": slot_details
    }


# ================== VIBER NOTIFICATION (PLACEHOLDER) ==================

async def send_viber_notification(phone: str, message: str) -> bool:
    """
    Placeholder for Viber API integration.
    Will be implemented when Viber Bot API credentials are configured.

    Args:
        phone: Client phone number (normalized)
        message: Notification message text

    Returns:
        True if message sent successfully, False otherwise
    """
    logger.info(f"[VIBER PLACEHOLDER] To: {phone}, Message: {message}")
    return False


async def send_booking_confirmation_viber(phone: str, booking_id: str, date: str, time: str, services: List[str]) -> bool:
    """
    Placeholder: Send booking confirmation via Viber.
    """
    service_list = ", ".join(services)
    message = f"Potvrda rezervacije #{booking_id}\nDatum: {date}\nVreme: {time}\nUsluge: {service_list}"
    return await send_viber_notification(phone, message)


async def send_booking_reminder_viber(phone: str, booking_id: str, date: str, time: str) -> bool:
    """
    Placeholder: Send booking reminder via Viber (e.g., 24h before).
    """
    message = f"Podsetnik: Vaš termin #{booking_id} je sutra {date} u {time}."
    return await send_viber_notification(phone, message)
