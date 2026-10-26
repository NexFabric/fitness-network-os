"""Trainer↔member assignment management.

Gated on ``staff:write``, which TRAINER does not hold — a trainer cannot widen
its own view by assigning members to itself.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService
from app.models.user import User
from app.services.member import MemberService
from app.services.trainer_assignment import TrainerAssignmentService

router = APIRouter()


class TrainerAssignmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    trainer_user_id: UUID
    member_id: UUID
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignMemberRequest(BaseModel):
    member_id: UUID


@router.get(
    "/{trainer_user_id}/members",
    response_model=list[TrainerAssignmentResponse],
)
async def list_trainer_members(
    trainer_user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Staff read the roster; a trainer may read its own without staff:read."""
    if current_user.id != trainer_user_id:
        AuthorizationService.require_tenant(current_user, "staff:read", tenant_id)
    return await TrainerAssignmentService(db).list_for_trainer(
        tenant_id, trainer_user_id
    )


@router.post(
    "/{trainer_user_id}/members",
    response_model=TrainerAssignmentResponse,
    status_code=201,
)
async def assign_member_to_trainer(
    trainer_user_id: UUID,
    body: AssignMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    AuthorizationService.require_tenant(current_user, "staff:write", tenant_id)

    # Prove the member belongs to this tenant before creating the link, so a
    # foreign member_id cannot be smuggled in via the request body.
    member = await MemberService(db).get_member(tenant_id, body.member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="member_not_found")

    from app.services.staff import StaffService

    if not await StaffService.is_employed(db, tenant_id, trainer_user_id):
        raise HTTPException(status_code=400, detail="trainer_not_employed")

    assignment = await TrainerAssignmentService(db).assign(
        tenant_id, trainer_user_id, body.member_id
    )
    await db.commit()
    await db.refresh(assignment)
    return assignment


@router.delete("/{trainer_user_id}/members/{member_id}", status_code=204)
async def unassign_member_from_trainer(
    trainer_user_id: UUID,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    AuthorizationService.require_tenant(current_user, "staff:write", tenant_id)
    removed = await TrainerAssignmentService(db).unassign(
        tenant_id, trainer_user_id, member_id
    )
    if not removed:
        raise HTTPException(status_code=404, detail="assignment_not_found")
    await db.commit()
