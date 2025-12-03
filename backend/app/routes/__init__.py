from fastapi import APIRouter

from . import health

core_router = APIRouter()

# All health endpoints will be under /api/v1/health
core_router.include_router(health.router, prefix="/health", tags=["health"])