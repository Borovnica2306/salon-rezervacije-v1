"""
Tenant resolution and middleware for multitenant support.
"""
import logging
from fastapi import Request, HTTPException
from database import db

logger = logging.getLogger(__name__)

DEFAULT_FEATURES = {
    "viber_notifications": True,
    "ips_qr_payment": True,
    "manual_booking": True,
    "email_notifications": True,
    "lazy_cancel": True,
}


async def resolve_tenant_by_slug(slug: str) -> dict:
    """Resolve a tenant document from its slug."""
    tenant = await db.tenants.find_one({"slug": slug})
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Salon '{slug}' not found")
    tenant["id"] = str(tenant["_id"])
    return tenant


async def get_tenant_id_from_header(request: Request) -> str:
    """Extract tenant_id from X-Tenant-ID header."""
    tenant_id = request.headers.get("X-Tenant-ID", "")
    if not tenant_id:
        return ""
    # Verify tenant exists
    tenant = await db.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Invalid tenant")
    return tenant_id


def check_tenant_access(user: dict, tenant_id: str):
    """Verify user has access to the given tenant. Super admin can access all."""
    if user.get("role") == "super_admin":
        return
    user_tenant = user.get("tenant_id", "")
    if user_tenant != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this salon")
