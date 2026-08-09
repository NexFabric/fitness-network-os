from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.db.session import get_db
from app.models.user import User
from app.schemas.membership import (
    MembershipFreezeCreate,
    MembershipFreezeResponse,
    MembershipResponse,
)
from app.services.membership import MembershipService

router = APIRouter()

@router.post("/{membership_id}/freeze", response_model=MembershipFreezeResponse)
async def freeze_membership(
    membership_id: UUID,
    freeze_in: MembershipFreezeCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not AuthorizationService.is_authorized(user=current_user, permission="memberships:write", resource_tenant_id=tenant_id):
        raise SecurityException()
        
    service = MembershipService(db)
    try:
        freeze = await service.freeze_membership(
            membership_id=membership_id,
            start_date=freeze_in.start_date,
            expected_end_date=freeze_in.expected_end_date,
            reason=freeze_in.reason,
            changed_by_user_id=current_user.id
        )
        await db.commit()
        await db.refresh(freeze)
        return freeze
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{membership_id}/unfreeze", response_model=MembershipResponse)
async def unfreeze_membership(
    membership_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not AuthorizationService.is_authorized(user=current_user, permission="memberships:write", resource_tenant_id=tenant_id):
        raise SecurityException()

    service = MembershipService(db)
    try:
        membership = await service.unfreeze_membership(
            membership_id=membership_id,
            changed_by_user_id=current_user.id
        )
        await db.commit()
        await db.refresh(membership)
        return membership
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
