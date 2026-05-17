import string
import random
import logging
import io
import qrcode
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from bson import ObjectId
from database import db, MASTER_CATEGORIES

logger = logging.getLogger(__name__)

# ================== SERBIAN TRANSLITERATION ==================

_SERBIAN_MAP = {
    'č': 'C', 'Č': 'C', 'ć': 'C', 'Ć': 'C',
    'š': 'S', 'Š': 'S', 'ž': 'Z', 'Ž': 'Z',
    'đ': 'Dj', 'Đ': 'DJ',
}

def transliterate_serbian(text: str) -> str:
    for src, dst in _SERBIAN_MAP.items():
        text = text.replace(src, dst)
    return text.upper()


def clean_bank_account(account: str) -> str:
    return account.replace(' ', '').replace('-', '').ljust(18, '0')[:18]


def format_ips_amount(amount: float) -> str:
    return f"RSD{amount:,.2f}".replace(',', '_').replace('.', ',').replace('_', '')


def generate_ips_qr_string(
    bank_account: str,
    recipient_name: str,
    amount: float,
    booking_id: str,
) -> str:
    account = clean_bank_account(bank_account)
    name = transliterate_serbian(recipient_name)
    ips_amount = format_ips_amount(amount)
    purpose = transliterate_serbian(f"Avans za rezervaciju ID {booking_id}")
    reference = f"99{booking_id}"

    return '|'.join([
        'K:PR',
        'V:01',
        'C:1',
        f'R:{account}',
        f'N:{name}',
        f'I:{ips_amount}',
        'SF:289',
        f'S:{purpose}',
        f'RO:{reference}',
    ])


def generate_ips_qr_image(
    bank_account: str,
    recipient_name: str,
    amount: float,
    booking_id: str,
) -> bytes:
    qr_string = generate_ips_qr_string(bank_account, recipient_name, amount, booking_id)
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(qr_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

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

    # Find the widest possible work window (for slot generation loop)
    # Individual per-worker boundary checks happen inside check_sequential_availability
    min_start = 24 * 60
    max_end = 0
    worker_hours = {}

    for wid in worker_ids:
        w = worker_map.get(wid)
        if w:
            ws = time_to_minutes(w.get("work_start", default_start))
            we = time_to_minutes(w.get("work_end", default_end))
            worker_hours[wid] = (ws, we)
            min_start = min(min_start, ws)
            max_end = max(max_end, we)

    if min_start >= max_end:
        return {"slots": []}

    # Calculate total duration of all services
    total_duration = sum(service_duration.get(p["service_id"], 0) for p in service_worker_pairs)

    # Total chain duration = service durations + buffers between them
    num_buffers = max(0, len(service_worker_pairs) - 1)
    total_chain_duration = total_duration + (num_buffers * SOCIAL_BUFFER)

    def is_worker_available(wid: str, start: int, end: int) -> bool:
        w = worker_map.get(wid)
        if not w:
            return False

        # Check worker's own work hours boundary
        ws, we = worker_hours.get(wid, (0, 24 * 60))
        if start < ws or end > we:
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
        Each worker's own work hours are checked individually.
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

            # Worker must be available (includes their own work hours boundary check)
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


# ================== VIBER DIRECT CHAT ==================
# Viber Bot API removed (Viber changed pricing model).
# Instead, we use direct viber://chat links with the salon phone number.


# ================== LAZY CANCEL (STALE UNPAID) ==================

UNPAID_CANCEL_HOURS = 3


async def cancel_stale_unpaid_reservations() -> int:
    """
    Cancel reservations where payment_status is 'pending'
    and created_at is older than UNPAID_CANCEL_HOURS.
    Returns the number of cancelled reservations.
    """
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=UNPAID_CANCEL_HOURS)).isoformat()

        result = await db.reservations.update_many(
            {
                "status": {"$ne": "cancelled"},
                "payment_status": "pending",
                "created_at": {"$lt": cutoff},
            },
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_by": "system_auto",
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
        count = result.modified_count
        if count > 0:
            logger.info(f"[LAZY-CANCEL] Auto-cancelled {count} stale unpaid reservation(s)")
        return count
    except Exception as e:
        logger.error(f"[LAZY-CANCEL] Error: {e}")
        return 0


# ================== DAILY REMINDERS ==================

async def process_daily_reminders() -> dict:
    """
    Count tomorrow's reservations by payment status.
    Viber Bot API removed — reminders now serve as a dashboard summary only.
    """
    belgrade_tz = timezone(timedelta(hours=2))
    tomorrow = (datetime.now(belgrade_tz) + timedelta(days=1)).strftime("%Y-%m-%d")

    reservations = await db.reservations.find({
        "date": tomorrow,
        "status": {"$ne": "cancelled"},
    }).to_list(500)

    confirmed_count = 0
    pending_count = 0

    for r in reservations:
        payment = r.get("payment_status", "pending")
        if payment in ("confirmed", "paid", "sent_for_verification"):
            confirmed_count += 1
        else:
            pending_count += 1

    logger.info(
        f"[REMINDERS] Tomorrow={tomorrow}: "
        f"total={len(reservations)}, confirmed={confirmed_count}, pending={pending_count}"
    )
    return {
        "date": tomorrow,
        "total_reservations": len(reservations),
        "confirmed": confirmed_count,
        "pending": pending_count,
    }
