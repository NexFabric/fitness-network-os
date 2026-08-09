import logging
from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import (
    Membership,
    MembershipPeriod,
    MembershipRenewal,
    PlanVersion,
)
from app.services.membership import MembershipService

logger = logging.getLogger(__name__)

class ResolutionEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.membership_service = MembershipService(session)

    async def activate_scheduled_memberships(self):
        now = datetime.now(UTC)
        stmt = select(Membership.id).where(
            and_(
                Membership.start_date <= now,
                Membership.status == "SCHEDULED"
            )
        )
        result = await self.session.execute(stmt)
        membership_ids = result.scalars().all()

        for mid in membership_ids:
            async with self.session.begin_nested():
                try:
                    await self.membership_service.activate_scheduled_membership(mid)
                except Exception as e:
                    logger.error(f"Failed to activate membership {mid}: {e}")

    async def process_expirations(self):
        now = datetime.now(UTC)
        stmt = select(Membership.id).where(
            and_(
                Membership.end_date < now,
                Membership.status.in_(["ACTIVE", "PAST_DUE"])
            )
        )
        result = await self.session.execute(stmt)
        membership_ids = result.scalars().all()

        for mid in membership_ids:
            async with self.session.begin_nested():
                try:
                    await self.membership_service.expire_membership(mid)
                except Exception as e:
                    logger.error(f"Failed to expire membership {mid}: {e}")

    async def process_renewals(self):
        now = datetime.now(UTC)
        stmt = select(MembershipRenewal.id, MembershipRenewal.membership_id).where(
            and_(
                MembershipRenewal.renewal_date <= now,
                MembershipRenewal.status == "PENDING"
            )
        )
        result = await self.session.execute(stmt)
        renewals = result.all()

        for rid, mid in renewals:
            async with self.session.begin_nested():
                try:
                    renewal_stmt = select(MembershipRenewal).where(MembershipRenewal.id == rid).with_for_update()
                    renewal = (await self.session.execute(renewal_stmt)).scalar_one()
                    
                    if renewal.status != "PENDING":
                        continue
                        
                    membership = await self.membership_service.get_membership(mid, for_update=True)
                    if not membership:
                        continue
                        
                    pv_stmt = select(PlanVersion).where(PlanVersion.id == renewal.next_plan_version_id)
                    pv = (await self.session.execute(pv_stmt)).scalar_one_or_none()
                    if pv:
                        membership.plan_version_id = renewal.next_plan_version_id
                        
                        if membership.end_date:
                            from dateutil.relativedelta import relativedelta
                            
                            stmt_active_period = select(MembershipPeriod).where(
                                MembershipPeriod.membership_id == membership.id,
                                MembershipPeriod.is_active == True
                            )
                            active_period = (await self.session.execute(stmt_active_period)).scalar_one_or_none()
                            if active_period:
                                active_period.is_active = False
                                
                            new_end_date = membership.end_date + relativedelta(months=pv.billing_cycle_months)
                            
                            period = MembershipPeriod(
                                membership_id=membership.id,
                                start_date=membership.end_date,
                                end_date=new_end_date,
                                is_active=membership.status == "ACTIVE",
                                tenant_id=membership.tenant_id
                            )
                            self.session.add(period)
                            membership.end_date = new_end_date
                    
                    renewal.status = "PROCESSED"
                except Exception as e:
                    logger.error(f"Failed to process renewal {rid}: {e}")

    async def run_all(self):
        await self.activate_scheduled_memberships()
        await self.process_renewals()
        await self.process_expirations()
