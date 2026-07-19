"""
Shared utilities for all route modules.
"""
import os
import logging
import secrets
import string
from zoneinfo import ZoneInfo
from datetime import datetime
from fastapi import HTTPException, Request

from database import db

logger = logging.getLogger(__name__)

PI_API_KEY = os.environ.get("PI_API_KEY", "")
PI_API_BASE = "https://api.minepi.com/v2"

COUNTRY_TIMEZONES = {
    "RS": "Europe/Belgrade",
    "HR": "Europe/Zagreb",
    "BA": "Europe/Sarajevo",
    "ME": "Europe/Podgorica",
    "MK": "Europe/Skopje",
    "SI": "Europe/Ljubljana",
}


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def _get_tid(request: Request) -> str:
    """Extract tenant_id from X-Tenant-ID header."""
    tid = request.headers.get("X-Tenant-ID", "")
    if not tid:
        raise HTTPException(status_code=400, detail="Missing X-Tenant-ID header")
    return tid


async def _get_tid_optional(request: Request) -> str:
    """Extract tenant_id, return empty string if missing."""
    return request.headers.get("X-Tenant-ID", "")


async def _get_salon_today(tenant_id: str) -> str:
    """Get today's date string in the salon's timezone."""
    tenant = await db.tenants.find_one({"tenant_id": tenant_id})
    country = tenant.get("country", "RS") if tenant else "RS"
    tz_name = COUNTRY_TIMEZONES.get(country, "Europe/Belgrade")
    salon_now = datetime.now(ZoneInfo(tz_name))
    return salon_now.strftime("%Y-%m-%d")
