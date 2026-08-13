import re
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.staff import StaffService

router = APIRouter()

# Deliberately permissive: reject obvious nonsense without pretending to be an
# authority on what a valid address is.
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


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


class StaffAccountRequest(BaseModel):
    # Plain ``str`` with a shape check rather than ``EmailStr``: the project has
    # no email-validator dependency and ``LoginRequest`` already takes this
    # approach. Deliverability is proven by the colleague logging in, not here.
    email: str = Field(min_length=3, max_length=255)
    role: str = Field(default="STAFF")
    location_id: UUID | None = None

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_RE.fullmatch(normalized):
            raise ValueError("invalid_email")
        return normalized


class StaffAccountResponse(BaseModel):
    staff: StaffResponse
    user_id: UUID
    email: str
    # Returned exactly once, at creation. It is never stored in the clear and
    # cannot be read back — the administrator has to hand it over now.
    one_time_password: str


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


@router.post("/accounts", response_model=StaffAccountResponse, status_code=201)
async def create_staff_account(
    body: StaffAccountRequest,
    response: Response,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a login for a new colleague and link it to this tenant.

    The generated password is in the response body, so the response must not be
    cached anywhere on the way back to the administrator.
    """
    _require(current_user, tenant_id, "staff:write")
    svc = StaffService(db)
    try:
        provisioned = await svc.create_staff_account(
            tenant_id,
            email=body.email,
            role=body.role,
            location_id=body.location_id,
        )
    except ValueError as e:
        detail = str(e)
        status_code = 409 if detail == "email_already_registered" else 400
        raise HTTPException(status_code=status_code, detail=detail) from e

    await db.commit()
    await db.refresh(provisioned.staff)

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return StaffAccountResponse(
        staff=StaffResponse.model_validate(provisioned.staff),
        user_id=provisioned.user.id,
        email=provisioned.user.email,
        one_time_password=provisioned.one_time_password,
    )


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
