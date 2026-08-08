from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership, MembershipFreeze, StatusHistory


class MembershipService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_membership(self, membership_id: UUID) -> Optional[Membership]:
        """Fetch a membership by ID."""
        stmt = select(Membership).where(Membership.id == membership_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def freeze_membership(
        self,
        membership_id: UUID,
        start_date: datetime,
        expected_end_date: datetime,
        reason: Optional[str],
        changed_by_user_id: Optional[UUID] = None,
    ) -> MembershipFreeze:
        """
        Freeze a membership. Changes its status to 'FROZEN'.
        """
        membership = await self.get_membership(membership_id)
        if not membership:
            raise ValueError("Membership not found")
            
        if membership.status == "FROZEN":
            raise ValueError("Membership is already frozen")

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
        history = StatusHistory(
            membership_id=membership_id,
            old_status=membership.status,
            new_status="FROZEN",
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id
        )
        self.session.add(history)

        # 3. Update Membership
        membership.status = "FROZEN"

        await self.session.commit()
        await self.session.refresh(freeze)
        return freeze

    async def unfreeze_membership(
        self,
        membership_id: UUID,
        changed_by_user_id: Optional[UUID] = None,
    ) -> Membership:
        """
        Unfreeze a membership manually. Changes status back to 'ACTIVE'
        and updates the freeze record's actual_end_date.
        """
        membership = await self.get_membership(membership_id)
        if not membership:
            raise ValueError("Membership not found")

        if membership.status != "FROZEN":
            raise ValueError("Membership is not frozen")

        # Find active freeze
        stmt = select(MembershipFreeze).where(
            MembershipFreeze.membership_id == membership_id,
            MembershipFreeze.actual_end_date.is_(None)
        )
        result = await self.session.execute(stmt)
        freeze = result.scalar_one_or_none()

        if freeze:
            now = datetime.now(UTC)
            freeze.actual_end_date = now
            
            # Recalculate end_date logic would go here:
            # delta = now - freeze.start_date
            # if membership.end_date:
            #     membership.end_date += delta
        
        # Record Status History
        history = StatusHistory(
            membership_id=membership_id,
            old_status="FROZEN",
            new_status="ACTIVE",
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id
        )
        self.session.add(history)

        membership.status = "ACTIVE"
        
        await self.session.commit()
        await self.session.refresh(membership)
        return membership
