import logging
import re
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.invite import PURPOSE_STAFF
from app.models.user import User
from app.services.invite import InviteService
from app.services.notification import NotificationService
from app.services.staff import StaffService

logger = logging.getLogger(__name__)

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
    email: str | None = None

    model_config = {"from_attributes": True}


def _staff_response(staff, email: str | None) -> StaffResponse:
    return StaffResponse(
        id=staff.id,
        tenant_id=staff.tenant_id,
        user_id=staff.user_id,
        role=staff.role,
        location_id=staff.location_id,
        created_at=staff.created_at,
        email=email,
    )


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
    # Raw invite shown once. The standing password is never returned.
    invite_token: str | None = None


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
        return _staff_response(staff, await svc.get_user_email(staff.user_id))
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

    The invite token is in the response body, so the response must not be
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
        status_code = 400
        raise HTTPException(status_code=status_code, detail=detail) from e

    try:
        _invite, invite_token = await InviteService(db).issue(
            tenant_id,
            provisioned.user.id,
            purpose=PURPOSE_STAFF,
        )
    except Exception as e:
        logger.exception(
            "staff.account.created invite issue failed user_id=%s",
            provisioned.user.id,
        )
        raise HTTPException(status_code=500, detail="invite_issue_failed") from e

    await db.commit()
    await db.refresh(provisioned.staff)

    # Best-effort hook: account creation must not fail if email cannot be queued.
    try:
        invite_line = (
            f"Parolanızı şu davet yolundan belirleyin (7 gün, bir kez):\n"
            f"/invite?token={invite_token}"
            if invite_token
            else "Yöneticinizden davet bağlantısını isteyin."
        )
        await NotificationService(db).schedule_delivery(
            tenant_id,
            channel="EMAIL",
            recipient_address=provisioned.user.email,
            recipient_user_id=provisioned.user.id,
            subject="GymClubNex personel hesabı",
            body=(
                "Hesabınız açıldı.\n\n"
                f"{invite_line}"
            ),
            context={"kind": "staff_account_created"},
            source_event_type="staff.account.created.v1",
            source_event_id=str(provisioned.staff.id),
            dedupe_key=f"staff-account-created:{provisioned.user.id}",
        )
        await db.commit()
    except Exception:
        logger.exception(
            "staff.account.created notification schedule failed user_id=%s",
            provisioned.user.id,
        )

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return StaffAccountResponse(
        staff=_staff_response(provisioned.staff, provisioned.user.email),
        user_id=provisioned.user.id,
        email=provisioned.user.email,
        invite_token=invite_token,
    )


@router.get("", response_model=list[StaffResponse])
async def list_staff(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "staff:read")
    rows = await StaffService(db).list_staff_with_emails(tenant_id)
    return [_staff_response(staff, email) for staff, email in rows]


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "staff:read")
    svc = StaffService(db)
    staff = await svc.get_staff(tenant_id, staff_id)
    if staff is None:
        raise HTTPException(status_code=404, detail="staff_not_found")
    return _staff_response(staff, await svc.get_user_email(staff.user_id))
