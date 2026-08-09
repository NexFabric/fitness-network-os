from fastapi import APIRouter

from app.api.v1.endpoints import entitlements, memberships

api_router = APIRouter()
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(entitlements.router, prefix="/members", tags=["entitlements"])
