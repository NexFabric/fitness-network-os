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
from app.models.tenant import Tenant
from app.services.entitlement import EntitlementService
from app.services.membership import MembershipService

logger = logging.getLogger(__name__)


class ResolutionEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.membership_service = MembershipService(session)

    async def run_for_tenant(self, tenant_id: UUID) -> None:
        # Parameterized SET LOCAL to avoid string interpolation of session GUC
        await self.session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        await self.activate_scheduled_memberships(tenant_id)
        await self.process_renewals(tenant_id)
        await self.process_expirations(tenant_id)

    async def activate_scheduled_memberships(self, tenant_id: UUID) -> None:
        now = datetime.now(UTC)
        stmt = select(Membership.id).where(
            and_(
                Membership.tenant_id == tenant_id,
                Membership.start_date <= now,
                Membership.status == "SCHEDULED",
            )
        )
        result = await self.session.execute(stmt)
        membership_ids = result.scalars().all()

        for mid in membership_ids:
            try:
                async with self.session.begin_nested():
                    # MembershipService.activate_scheduled_membership allocates wallets
                    await self.membership_service.activate_scheduled_membership(mid)
            except Exception as e:
                logger.error("Failed to activate membership %s: %s", mid, e)

    async def process_expirations(self, tenant_id: UUID) -> None:
        now = datetime.now(UTC)
        stmt = select(Membership.id).where(
            and_(
                Membership.tenant_id == tenant_id,
                Membership.end_date < now,
                Membership.status.in_(["ACTIVE", "PAST_DUE"]),
            )
        )
        result = await self.session.execute(stmt)
        membership_ids = result.scalars().all()

        for mid in membership_ids:
            try:
                async with self.session.begin_nested():
                    await self.membership_service.expire_membership(mid)
            except Exception as e:
                logger.error("Failed to expire membership %s: %s", mid, e)

    async def process_renewals(self, tenant_id: UUID) -> None:
        now = datetime.now(UTC)
        stmt = select(MembershipRenewal.id, MembershipRenewal.membership_id).where(
            and_(
                MembershipRenewal.tenant_id == tenant_id,
                MembershipRenewal.renewal_date <= now,
                MembershipRenewal.status == RenewalStatus.PENDING.value,
            )
        )
        result = await self.session.execute(stmt)
        renewals = result.all()

        for rid, mid in renewals:
            try:
                async with self.session.begin_nested():
                    renewal_stmt = (
                        select(MembershipRenewal)
                        .where(MembershipRenewal.id == rid)
                        .with_for_update()
                    )
                    renewal = (await self.session.execute(renewal_stmt)).scalar_one()

                    if renewal.status != RenewalStatus.PENDING.value:
                        continue

                    renewal.status = RenewalStatus.PROCESSING.value
                    await self.session.flush()

                    membership = await self.membership_service.get_membership(
                        mid, for_update=True
                    )
                    if not membership:
                        renewal.status = RenewalStatus.FAILED.value
                        continue

                    if not renewal.next_plan_version_id:
                        renewal.status = RenewalStatus.FAILED.value
                        continue

                    pv_stmt = select(PlanVersion).where(
                        PlanVersion.id == renewal.next_plan_version_id
                    )
                    pv = (await self.session.execute(pv_stmt)).scalar_one_or_none()
                    if not pv:
                        renewal.status = RenewalStatus.FAILED.value
                        continue

                    membership.plan_version_id = renewal.next_plan_version_id
                    membership.price_snapshot = pv.price_amount_minor
                    membership.price_snapshot_currency = pv.currency
                    membership.terms_snapshot = pv.terms

                    if membership.end_date:
                        from dateutil.relativedelta import relativedelta

                        stmt_active_period = select(MembershipPeriod).where(
                            MembershipPeriod.membership_id == membership.id,
                            MembershipPeriod.is_active.is_(True),
                        )
                        active_period = (
                            await self.session.execute(stmt_active_period)
                        ).scalar_one_or_none()
                        if active_period:
                            active_period.is_active = False

                        new_end_date = membership.end_date + relativedelta(
                            months=pv.billing_cycle_months
                        )

                        period = MembershipPeriod(
                            membership_id=membership.id,
                            start_date=membership.end_date,
                            end_date=new_end_date,
                            is_active=membership.status == "ACTIVE",
                            tenant_id=membership.tenant_id,
                        )
                        self.session.add(period)
                        membership.end_date = new_end_date

                    await EntitlementService.grant_from_plan_version(
                        self.session,
                        membership,
                        pv.id,
                        reason="renewal",
                    )

                    renewal.status = RenewalStatus.APPLIED.value
            except Exception as e:
                logger.error("Failed to process renewal %s: %s", rid, e)
                try:
                    async with self.session.begin_nested():
                        renewal_stmt = (
                            select(MembershipRenewal)
                            .where(MembershipRenewal.id == rid)
                            .with_for_update()
                        )
                        renewal = (
                            await self.session.execute(renewal_stmt)
                        ).scalar_one()
                        renewal.status = RenewalStatus.FAILED.value
                except Exception as ex:
                    logger.error("Failed to mark renewal %s as failed: %s", rid, ex)

    async def run_all(self) -> None:
        """Run resolution for every tenant (cron entrypoint)."""
        result = await self.session.execute(select(Tenant.id))
        tenant_ids = result.scalars().all()
        for tid in tenant_ids:
            try:
                async with self.session.begin_nested():
                    await self.run_for_tenant(tid)
            except Exception as e:
                logger.error("Resolution failed for tenant %s: %s", tid, e)
