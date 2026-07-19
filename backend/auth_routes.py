"""
Auth routes: login, logout, me, change-password.
"""
import logging
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from bson import ObjectId

from database import db
from models import LoginRequest
from auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, get_current_user,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/auth/login")
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
        "access_token": access_token,
        "worker_id": user.get("worker_id", ""),
        "language_preference": user.get("language_preference", "sr"),
        "must_change_password": user.get("must_change_password", False),
    }


@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out successfully"}


@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    # Add slug for frontend redirect
    tenant_id = user.get("tenant_id", "")
    if tenant_id and not user.get("slug"):
        tenant = await db.tenants.find_one({"tenant_id": tenant_id}, {"slug": 1})
        if tenant:
            user["slug"] = tenant["slug"]
    # Ensure worker fields are present
    if "worker_id" not in user:
        user["worker_id"] = ""
    if "language_preference" not in user:
        user["language_preference"] = "sr"
    if "must_change_password" not in user:
        user["must_change_password"] = False
    return user


@router.put("/auth/change-password")
async def change_password(request: Request, user: dict = Depends(get_current_user)):
    """Worker changes their temporary password."""
    body = await request.json()
    new_password = body.get("new_password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Lozinka mora imati najmanje 6 karaktera.")

    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {
            "password_hash": hash_password(new_password),
            "must_change_password": False,
        }}
    )
    return {"message": "Lozinka uspešno promenjena."}
