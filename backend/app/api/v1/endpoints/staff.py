from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.staff import StaffService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


class StaffLinkRequest(BaseModel):
    user_id: UUID
    role: str = Field(default="STAFF")
    location_id: UUID | None = None


class StaffResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    role: str
    location_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=StaffResponse, status_code=201)
async def link_staff(
    body: StaffLinkRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "staff:write")
    svc = StaffService(db)
    try:
        staff = await svc.link_staff(
            tenant_id,
            user_id=body.user_id,
            role=body.role,
            location_id=body.location_id,
        )
        await db.commit()
        await db.refresh(staff)
        return staff
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=list[StaffResponse])
async def list_staff(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "staff:read")
    return await StaffService(db).list_staff(tenant_id)


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "staff:read")
    staff = await StaffService(db).get_staff(tenant_id, staff_id)
    if staff is None:
        raise HTTPException(status_code=404, detail="staff_not_found")
    return staff
