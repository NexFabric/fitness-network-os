"""Trainer↔member assignments — the data behind ``Scope.ASSIGNED``.

A reader holding ``members:read`` but not ``members:read:all`` (today: TRAINER)
sees only members assigned to it here. Every query is tenant-filtered on top of
RLS, per the project rule that isolation never rests on RLS alone.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trainer_assignment import TrainerAssignment


class TrainerAssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def assigned_member_ids(
        self, tenant_id: UUID, trainer_user_id: UUID
    ) -> list[UUID]:
        result = await self.db.execute(
            select(TrainerAssignment.member_id).where(
                TrainerAssignment.tenant_id == tenant_id,
                TrainerAssignment.trainer_user_id == trainer_user_id,
                TrainerAssignment.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def is_assigned(
        self, tenant_id: UUID, trainer_user_id: UUID, member_id: UUID
    ) -> bool:
        result = await self.db.execute(
            select(TrainerAssignment.id).where(
                TrainerAssignment.tenant_id == tenant_id,
                TrainerAssignment.trainer_user_id == trainer_user_id,
                TrainerAssignment.member_id == member_id,
                TrainerAssignment.is_active.is_(True),
            )
        )
        return result.scalars().first() is not None

    async def list_for_trainer(
        self, tenant_id: UUID, trainer_user_id: UUID
    ) -> list[TrainerAssignment]:
        result = await self.db.execute(
            select(TrainerAssignment)
            .where(
                TrainerAssignment.tenant_id == tenant_id,
                TrainerAssignment.trainer_user_id == trainer_user_id,
                TrainerAssignment.is_active.is_(True),
            )
            .order_by(TrainerAssignment.created_at.desc())
        )
        return list(result.scalars().all())

    async def assign(
        self, tenant_id: UUID, trainer_user_id: UUID, member_id: UUID
    ) -> TrainerAssignment:
        """Idempotent: re-assigning an already-live pair returns the existing row."""
        existing = await self.db.execute(
            select(TrainerAssignment).where(
                TrainerAssignment.tenant_id == tenant_id,
                TrainerAssignment.trainer_user_id == trainer_user_id,
                TrainerAssignment.member_id == member_id,
            )
        )
        row = existing.scalars().first()
        if row is not None:
            row.is_active = True
            await self.db.flush()
            return row

        assignment = TrainerAssignment(
            tenant_id=tenant_id,
            trainer_user_id=trainer_user_id,
            member_id=member_id,
            is_active=True,
        )
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def unassign(
        self, tenant_id: UUID, trainer_user_id: UUID, member_id: UUID
    ) -> bool:
        """Soft-revoke so the assignment history survives. True when a row changed."""
        result = await self.db.execute(
            select(TrainerAssignment).where(
                TrainerAssignment.tenant_id == tenant_id,
                TrainerAssignment.trainer_user_id == trainer_user_id,
                TrainerAssignment.member_id == member_id,
                TrainerAssignment.is_active.is_(True),
            )
        )
        row = result.scalars().first()
        if row is None:
            return False
        row.is_active = False
        await self.db.flush()
        return True
