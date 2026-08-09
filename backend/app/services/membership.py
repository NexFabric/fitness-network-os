from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership, MembershipFreeze, MembershipStatusHistory


class MembershipService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_membership(self, membership_id: UUID, for_update: bool = False) -> Membership | None:
        """Fetch a membership by ID."""
        stmt = select(Membership).where(Membership.id == membership_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def freeze_membership(
        self,
        membership_id: UUID,
        start_date: datetime,
        expected_end_date: datetime,
        reason: str | None,
        changed_by_user_id: UUID | None = None,
    ) -> MembershipFreeze:
        """
        Freeze a membership. Changes its status to 'FROZEN'.
        """
        if expected_end_date <= start_date:
            raise ValueError("expected_end_date must be after start_date")

        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")
            
        if membership.status in ("FROZEN", "CANCELLED", "EXPIRED", "DRAFT"):
            raise ValueError(f"Membership status '{membership.status}' cannot be frozen")

        # 1. Create Freeze Record
        freeze = MembershipFreeze(
            membership_id=membership_id,
            start_date=start_date,
            expected_end_date=expected_end_date,
            reason=reason,
            tenant_id=membership.tenant_id
        )
        self.session.add(freeze)

        # 2. Record Status History
        history = MembershipStatusHistory(
            membership_id=membership_id,
            old_status=membership.status,
            new_status="FROZEN",
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id
        )
        self.session.add(history)

        membership.status = "FROZEN"

        await self.session.flush()
        return freeze

    async def unfreeze_membership(
        self,
        membership_id: UUID,
        changed_by_user_id: UUID | None = None,
    ) -> Membership:
        """
        Unfreeze a membership manually. Changes status back to 'ACTIVE'
        and updates the freeze record's actual_end_date.
        """
        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")

        if membership.status != "FROZEN":
            raise ValueError("Membership is not frozen")

        # Find active freeze
        stmt = select(MembershipFreeze).where(
            MembershipFreeze.membership_id == membership_id,
            MembershipFreeze.actual_end_date.is_(None)
        ).with_for_update()
        result = await self.session.execute(stmt)
        freeze = result.scalar_one_or_none()

        if not freeze:
            raise ValueError("No active freeze record found")

        now = datetime.now(UTC)
        freeze.actual_end_date = now
        
        # Extend membership end_date by the duration of the freeze
        if membership.end_date:
            delta = now - freeze.start_date
            membership.end_date += delta
        
        # Record Status History
        history = MembershipStatusHistory(
            membership_id=membership_id,
            old_status="FROZEN",
            new_status="ACTIVE",
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id
        )
        self.session.add(history)

        membership.status = "ACTIVE"
        
        await self.session.flush()
        return membership
