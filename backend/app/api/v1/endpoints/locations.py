from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.location import LocationService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    timezone: str = "UTC"
    address: str | None = None


class LocationUpdate(BaseModel):
    name: str | None = None
    timezone: str | None = None
    address: str | None = None


class LocationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    timezone: str
    address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=LocationResponse, status_code=201)
async def create_location(
    body: LocationCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "locations:write")
    svc = LocationService(db)
    try:
        loc = await svc.create_location(
            tenant_id,
            name=body.name,
            timezone=body.timezone,
            address=body.address,
        )
        await db.commit()
        await db.refresh(loc)
        return loc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=list[LocationResponse])
async def list_locations(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "locations:read")
    return await LocationService(db).list_locations(tenant_id)


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "locations:read")
    loc = await LocationService(db).get_location(tenant_id, location_id)
    if loc is None:
        raise HTTPException(status_code=404, detail="location_not_found")
    return loc


@router.patch("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    body: LocationUpdate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "locations:write")
    svc = LocationService(db)
    try:
        loc = await svc.update_location(
            tenant_id,
            location_id,
            name=body.name,
            timezone=body.timezone,
            address=body.address,
        )
        await db.commit()
        await db.refresh(loc)
        return loc
    except ValueError as e:
        code = 404 if str(e) == "location_not_found" else 400
        raise HTTPException(status_code=code, detail=str(e)) from e
