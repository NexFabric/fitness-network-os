"""Plan catalogue: the missing half of the membership domain.

Every membership row points at a ``plan_version``, but nothing over HTTP could
create one — memberships existed only where a seed script had written them, and
the whole lifecycle surface (freeze, cancel, renew) had no way to acquire
something to act on.

Authorisation reuses ``memberships:read`` / ``memberships:write`` rather than
introducing a ``plans:*`` pair: a plan version is the priced definition a
membership is sold against, held by exactly the roles that already sell them,
and a new permission would need a matrix migration to say the same thing.

Prices are integer minor units (kuruş) end to end — no float ever touches money
(``scripts/check_no_money_floats.py``).
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.db.session import get_db
from app.models.user import User
from app.services.membership import MembershipService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class PlanResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class PlanVersionCreate(BaseModel):
    # Minor units only: 49900 is ₺499,00. A float here would be a rounding bug
    # waiting for a renewal to expose it.
    price_amount_minor: int = Field(ge=0)
    billing_cycle_months: int = Field(ge=1, le=60)
    currency: str = Field(default="TRY", min_length=3, max_length=3)
    terms: dict[str, Any] | None = None


class PlanVersionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    version: int
    price_amount_minor: int
    currency: str
    billing_cycle_months: int
    is_published: bool
    published_at: datetime | None

    model_config = {"from_attributes": True}


class MembershipStartRequest(BaseModel):
    member_id: UUID
    plan_version_id: UUID
    # Defaults to now; a future date schedules the membership instead of
    # activating it (the service decides, not the client).
    start_date: datetime | None = None


@router.post("", response_model=PlanResponse, status_code=201)
async def create_plan(
    body: PlanCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "memberships:write")
    svc = MembershipService(db)
    plan = await svc.create_plan(
        tenant_id, name=body.name, description=body.description
    )
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("", response_model=list[PlanResponse])
async def list_plans(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=200),
):
    _require(current_user, tenant_id, "memberships:read")
    return await MembershipService(db).list_plans(tenant_id, limit=limit)


@router.post("/{plan_id}/versions", response_model=PlanVersionResponse, status_code=201)
async def create_plan_version(
    plan_id: UUID,
    body: PlanVersionCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "memberships:write")
    svc = MembershipService(db)
    try:
        pv = await svc.create_plan_version(
            tenant_id,
            plan_id=plan_id,
            price_amount_minor=body.price_amount_minor,
            billing_cycle_months=body.billing_cycle_months,
            currency=body.currency,
            terms=body.terms,
        )
    except ValueError as e:
        code = 404 if str(e) == "Plan not found" else 400
        raise HTTPException(status_code=code, detail=str(e)) from e
    await db.commit()
    await db.refresh(pv)
    return pv


@router.get("/versions", response_model=list[PlanVersionResponse])
async def list_plan_versions(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    plan_id: UUID | None = Query(default=None),
    published_only: bool = Query(default=False),
):
    _require(current_user, tenant_id, "memberships:read")
    return await MembershipService(db).list_plan_versions(
        tenant_id, plan_id=plan_id, published_only=published_only
    )


@router.post("/versions/{plan_version_id}/publish", response_model=PlanVersionResponse)
async def publish_plan_version(
    plan_version_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publishing is one-way: a published version is what memberships were sold
    against, so it can never be edited or unpublished — draft a new version."""
    _require(current_user, tenant_id, "memberships:write")
    svc = MembershipService(db)
    try:
        pv = await svc.publish_plan_version(plan_version_id)
    except ValueError as e:
        code = 404 if str(e) == "Plan version not found" else 400
        raise HTTPException(status_code=code, detail=str(e)) from e
    await db.commit()
    await db.refresh(pv)
    return pv


# Membership creation lives here with the catalogue it depends on; the
# /memberships router only mutates rows that already exist.
membership_router = APIRouter()


@membership_router.post("", status_code=201)
async def start_membership(
    body: MembershipStartRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "memberships:write")
    svc = MembershipService(db)
    try:
        membership = await svc.start_membership(
            member_id=body.member_id,
            plan_version_id=body.plan_version_id,
            start_date=body.start_date or datetime.now(UTC),
            tenant_id=tenant_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    await db.commit()
    await db.refresh(membership)
    return {
        "id": str(membership.id),
        "member_id": str(membership.member_id),
        "plan_version_id": str(membership.plan_version_id),
        "status": membership.status,
        "start_date": membership.start_date,
        "end_date": membership.end_date,
        "price_snapshot": membership.price_snapshot,
        "price_snapshot_currency": membership.price_snapshot_currency,
    }
