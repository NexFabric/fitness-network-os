from fastapi import APIRouter

from app.api.v1.endpoints import memberships, entitlements

api_router = APIRouter()
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(entitlements.router, prefix="/members", tags=["entitlements"])
