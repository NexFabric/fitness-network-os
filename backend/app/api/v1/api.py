from fastapi import APIRouter

from app.api.v1.endpoints import access, entitlements, finance, memberships

api_router = APIRouter()
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(entitlements.router, prefix="/members", tags=["entitlements"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(access.router, prefix="/access", tags=["access"])
