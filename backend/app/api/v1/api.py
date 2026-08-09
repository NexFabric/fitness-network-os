from fastapi import APIRouter

from app.api.v1.endpoints import (
    access,
    entitlements,
    finance,
    locations,
    members,
    memberships,
    outbox,
    staff,
)

api_router = APIRouter()
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
api_router.include_router(members.router, prefix="/members", tags=["members"])
api_router.include_router(entitlements.router, prefix="/members", tags=["entitlements"])
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(access.router, prefix="/access", tags=["access"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(staff.router, prefix="/staff", tags=["staff"])
api_router.include_router(outbox.router, prefix="/outbox", tags=["outbox"])
