from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService
from app.models.onboarding import OnboardingStage, TenantOnboarding
from app.models.user import User

router = APIRouter()


class OnboardingStatusResponse(BaseModel):
    current_stage: OnboardingStage
    step_data: dict
    is_completed: bool
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class AdvanceStageRequest(BaseModel):
    next_stage: OnboardingStage
    stage_data: dict = {}


@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Retrieve current tenant setup/onboarding workflow stage."""
    AuthorizationService.require_tenant(current_user, "gym:read", tenant_id)

    onboarding = (
        await db.execute(
            select(TenantOnboarding).where(TenantOnboarding.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()

    if not onboarding:
        onboarding = TenantOnboarding(
            id=uuid4(),
            tenant_id=tenant_id,
            current_stage=OnboardingStage.ORG_CREATED,
            step_data={},
            is_completed=False,
        )
        db.add(onboarding)
        await db.commit()
        await db.refresh(onboarding)

    return onboarding


@router.post("/advance", response_model=OnboardingStatusResponse)
async def advance_onboarding_stage(
    req: AdvanceStageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Advance tenant onboarding to next milestone stage."""
    AuthorizationService.require_tenant(current_user, "gym:write", tenant_id)

    onboarding = (
        await db.execute(
            select(TenantOnboarding).where(TenantOnboarding.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()

    if not onboarding:
        onboarding = TenantOnboarding(
            id=uuid4(),
            tenant_id=tenant_id,
            current_stage=OnboardingStage.ORG_CREATED,
            step_data={},
            is_completed=False,
        )
        db.add(onboarding)
        await db.flush()

    # Verify stage prerequisites before advancing
    from fastapi import HTTPException
    from sqlalchemy import func

    from app.models.location import Location
    from app.models.membership import PlanVersion
    from app.models.rbac import UserRole

    if req.next_stage in {
        OnboardingStage.PLANS_DEFINED,
        OnboardingStage.STAFF_INVITED,
        OnboardingStage.COMPLETED,
    }:
        loc_count = (
            await db.execute(
                select(func.count(Location.id)).where(Location.tenant_id == tenant_id)
            )
        ).scalar() or 0
        if loc_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Önce en az bir şube (location) tanımlamalısınız.",
            )

    if req.next_stage in {
        OnboardingStage.STAFF_INVITED,
        OnboardingStage.COMPLETED,
    }:
        plan_count = (
            await db.execute(
                select(func.count(PlanVersion.id)).where(
                    PlanVersion.tenant_id == tenant_id,
                    PlanVersion.is_published.is_(True),
                )
            )
        ).scalar() or 0
        if plan_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Önce en az bir yayınlanmış üyelik paketi (plan) oluşturmalısınız.",
            )

    if req.next_stage == OnboardingStage.COMPLETED:
        staff_count = (
            await db.execute(
                select(func.count(UserRole.user_id)).where(
                    UserRole.tenant_id == tenant_id
                )
            )
        ).scalar() or 0
        if staff_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Önce en az bir personel veya yetkili kullanıcı atamalısınız.",
            )

    # Merge step data
    updated_data = dict(onboarding.step_data or {})
    updated_data[req.next_stage.value] = req.stage_data
    onboarding.step_data = updated_data
    onboarding.current_stage = req.next_stage

    if req.next_stage == OnboardingStage.COMPLETED:
        onboarding.is_completed = True
        onboarding.completed_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(onboarding)
    return onboarding
