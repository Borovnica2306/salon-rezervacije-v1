"""
Main router orchestrator — includes all domain-specific sub-routers.
"""
from fastapi import APIRouter

from auth_routes import router as auth_router
from worker_routes import router as worker_router
from admin_routes import router as admin_router
from booking_routes import router as booking_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(worker_router)
api_router.include_router(admin_router)
api_router.include_router(booking_router)
