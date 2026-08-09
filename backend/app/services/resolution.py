import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import (
    Membership,
    MembershipPeriod,
    MembershipRenewal,
    PlanVersion,
    RenewalStatus,
)
from app.services.membership import MembershipService

logger = logging.getLogger(__name__)

class ResolutionEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.membership_service = MembershipService(session)

    async def run_for_tenant(self, tenant_id: UUID):
        await self.session.execute(text("SET LOCAL app.current_tenant_id = :t_id"), {"t_id": str(tenant_id)})
        await self.activate_scheduled_memberships(tenant_id)
        await self.process_renewals(tenant_id)
        await self.process_expirations(tenant_id)

    async def activate_scheduled_memberships(self, tenant_id: UUID):
        now = datetime.now(UTC)
        stmt = select(Membership.id).where(
            and_(
                Membership.tenant_id == tenant_id,
                Membership.start_date <= now,
                Membership.status == "SCHEDULED"
            )
        )
        result = await self.session.execute(stmt)
        membership_ids = result.scalars().all()

        for mid in membership_ids:
            try:
                async with self.session.begin_nested():
                    await self.membership_service.activate_scheduled_membership(mid)
            except Exception as e:
                logger.error(f"Failed to activate membership {mid}: {e}")

    async def process_expirations(self, tenant_id: UUID):
        now = datetime.now(UTC)
        stmt = select(Membership.id).where(
            and_(
                Membership.tenant_id == tenant_id,
                Membership.end_date < now,
                Membership.status.in_(["ACTIVE", "PAST_DUE"])
            )
        )
        result = await self.session.execute(stmt)
        membership_ids = result.scalars().all()

        for mid in membership_ids:
            try:
                async with self.session.begin_nested():
                    await self.membership_service.expire_membership(mid)
            except Exception as e:
                logger.error(f"Failed to expire membership {mid}: {e}")

    async def process_renewals(self, tenant_id: UUID):
        now = datetime.now(UTC)
        stmt = select(MembershipRenewal.id, MembershipRenewal.membership_id).where(
            and_(
                MembershipRenewal.tenant_id == tenant_id,
                MembershipRenewal.renewal_date <= now,
                MembershipRenewal.status == RenewalStatus.PENDING.value
            )
        )
        result = await self.session.execute(stmt)
        renewals = result.all()

        for rid, mid in renewals:
            try:
                async with self.session.begin_nested():
                    renewal_stmt = select(MembershipRenewal).where(MembershipRenewal.id == rid).with_for_update()
                    renewal = (await self.session.execute(renewal_stmt)).scalar_one()
                    
                    if renewal.status != RenewalStatus.PENDING.value:
                        continue
                        
                    renewal.status = RenewalStatus.PROCESSING.value
                    await self.session.flush()

                    membership = await self.membership_service.get_membership(mid, for_update=True)
                    if not membership:
                        renewal.status = RenewalStatus.FAILED.value
                        continue
                        
                    pv_stmt = select(PlanVersion).where(PlanVersion.id == renewal.next_plan_version_id)
                    pv = (await self.session.execute(pv_stmt)).scalar_one_or_none()
                    if pv:
                        membership.plan_version_id = renewal.next_plan_version_id
                        membership.price_snapshot = pv.price_amount_minor
                        membership.price_snapshot_currency = pv.currency
                        membership.terms_snapshot = pv.terms
                        
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
                    
                    renewal.status = RenewalStatus.APPLIED.value
            except Exception as e:
                logger.error(f"Failed to process renewal {rid}: {e}")
                try:
                    async with self.session.begin_nested():
                        renewal_stmt = select(MembershipRenewal).where(MembershipRenewal.id == rid).with_for_update()
                        renewal = (await self.session.execute(renewal_stmt)).scalar_one()
                        renewal.status = RenewalStatus.FAILED.value
                except Exception as ex:
                    logger.error(f"Failed to mark renewal {rid} as failed: {ex}")

    async def run_all(self):
        # We replace this with a run_for_tenant based flow or keep it for backward compat in tests if needed
        # but tests will be rewritten.
        pass
