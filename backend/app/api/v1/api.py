from fastapi import APIRouter

from app.api.v1.endpoints import memberships

api_router = APIRouter()
api_router.include_router(memberships.router, prefix="/memberships", tags=["memberships"])
