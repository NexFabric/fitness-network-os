from datetime import UTC, datetime
from uuid import UUID

from dateutil.relativedelta import relativedelta
from sqlalchemy import exc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_types import MEMBERSHIP_ACTIVATED_V1
from app.models.membership import (
    Membership,
    MembershipCancellation,
    MembershipFreeze,
    MembershipPeriod,
    MembershipRenewal,
    MembershipStatusHistory,
    Plan,
    PlanVersion,
    RenewalStatus,
)


class MembershipService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_membership(
        self, membership_id: UUID, for_update: bool = False
    ) -> Membership | None:
        """Fetch a membership by ID."""
        stmt = select(Membership).where(Membership.id == membership_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_memberships_for_member(
        self,
        tenant_id: UUID,
        member_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Membership]:
        """List memberships for a single member within a tenant (self-service / staff)."""
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        stmt = (
            select(Membership)
            .where(
                Membership.tenant_id == tenant_id,
                Membership.member_id == member_id,
            )
            .order_by(Membership.start_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_plan(
        self, tenant_id: UUID, *, name: str, description: str | None = None
    ) -> Plan:
        plan = Plan(
            tenant_id=tenant_id, name=name, description=description, is_active=True
        )
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def list_plans(self, tenant_id: UUID, *, limit: int = 100) -> list[Plan]:
        stmt = (
            select(Plan)
            .where(Plan.tenant_id == tenant_id)
            .order_by(Plan.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_plan_versions(
        self,
        tenant_id: UUID,
        *,
        plan_id: UUID | None = None,
        published_only: bool = False,
    ) -> list[PlanVersion]:
        stmt = select(PlanVersion).where(PlanVersion.tenant_id == tenant_id)
        if plan_id is not None:
            stmt = stmt.where(PlanVersion.plan_id == plan_id)
        if published_only:
            stmt = stmt.where(PlanVersion.is_published.is_(True))
        stmt = stmt.order_by(PlanVersion.version.desc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def create_plan_version(
        self,
        tenant_id: UUID,
        *,
        plan_id: UUID,
        price_amount_minor: int,
        billing_cycle_months: int,
        currency: str = "TRY",
        terms: dict | None = None,
    ) -> PlanVersion:
        """Draft a new version of a plan.

        The version number is derived server-side rather than accepted from the
        caller: two operators drafting at once must not be able to agree on the
        same number, and a client-chosen version would let one silently take
        another's slot.
        """
        plan = (
            await self.session.execute(
                select(Plan).where(Plan.id == plan_id, Plan.tenant_id == tenant_id)
            )
        ).scalar_one_or_none()
        if not plan:
            raise ValueError("Plan not found")

        if price_amount_minor < 0:
            raise ValueError("Price cannot be negative")
        if billing_cycle_months < 1:
            raise ValueError("Billing cycle must be at least one month")

        latest = (
            await self.session.execute(
                select(PlanVersion.version)
                .where(
                    PlanVersion.plan_id == plan_id,
                    PlanVersion.tenant_id == tenant_id,
                )
                .order_by(PlanVersion.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        pv = PlanVersion(
            tenant_id=tenant_id,
            plan_id=plan_id,
            version=(latest or 0) + 1,
            price_amount_minor=price_amount_minor,
            currency=currency.upper(),
            billing_cycle_months=billing_cycle_months,
            terms=terms or {},
            is_published=False,
        )
        self.session.add(pv)
        await self.session.flush()
        return pv

    async def publish_plan_version(self, plan_version_id: UUID) -> PlanVersion:
        stmt = (
            select(PlanVersion)
            .where(PlanVersion.id == plan_version_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        pv = result.scalar_one_or_none()
        if not pv:
            raise ValueError("Plan version not found")
        if pv.is_published:
            raise ValueError("Plan version is already published")

        pv.is_published = True
        pv.published_at = datetime.now(UTC)
        await self.session.flush()
        return pv

    async def update_plan_version(self, plan_version_id: UUID, **kwargs) -> PlanVersion:
        stmt = (
            select(PlanVersion)
            .where(PlanVersion.id == plan_version_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        pv = result.scalar_one_or_none()
        if not pv:
            raise ValueError("Plan version not found")

        if pv.is_published:
            raise ValueError("Cannot update published PlanVersion")

        for k, v in kwargs.items():
            if hasattr(pv, k):
                setattr(pv, k, v)

        await self.session.flush()
        return pv

    async def start_membership(
        self,
        member_id: UUID,
        plan_version_id: UUID,
        start_date: datetime,
        tenant_id: UUID,
    ) -> Membership:
        # Check for overlap
        stmt = select(Membership).where(
            Membership.member_id == member_id,
            Membership.status.in_(
                {"ACTIVE", "FROZEN", "PAST_DUE", "SCHEDULED", "PENDING"}
            ),
        )
        existing = await self.session.execute(stmt)
        if existing.scalars().first():
            raise ValueError("Member already has an active or scheduled membership")

        pv_stmt = select(PlanVersion).where(PlanVersion.id == plan_version_id)
        pv = (await self.session.execute(pv_stmt)).scalar_one_or_none()
        if not pv or not pv.is_published:
            raise ValueError("Valid published PlanVersion required")

        status = "ACTIVE" if start_date <= datetime.now(UTC) else "SCHEDULED"
        end_date = start_date + relativedelta(months=pv.billing_cycle_months)

        membership = Membership(
            member_id=member_id,
            plan_version_id=plan_version_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            price_snapshot=pv.price_amount_minor,
            price_snapshot_currency=pv.currency,
            terms_snapshot=pv.terms,
            tenant_id=tenant_id,
        )
        self.session.add(membership)
        await self.session.flush()

        period = MembershipPeriod(
            membership_id=membership.id,
            start_date=start_date,
            end_date=end_date,
            is_active=status == "ACTIVE",
            tenant_id=tenant_id,
        )
        self.session.add(period)

        history = MembershipStatusHistory(
            membership_id=membership.id,
            old_status="DRAFT",
            new_status=status,
            changed_at=datetime.now(UTC),
            tenant_id=tenant_id,
        )
        self.session.add(history)
        await self.session.flush()

        if status == "ACTIVE":
            from app.services.outbox import OutboxService

            await OutboxService(self.session).enqueue(
                tenant_id=tenant_id,
                event_type=MEMBERSHIP_ACTIVATED_V1,
                payload={
                    "membership_id": str(membership.id),
                    "member_id": str(member_id),
                    "plan_version_id": str(plan_version_id),
                    "status": status,
                },
                aggregate_type="membership",
                aggregate_id=membership.id,
                dedupe_key=f"membership.activated:{membership.id}",
            )

        return membership

    async def freeze_membership(
        self,
        membership_id: UUID,
        start_date: datetime,
        expected_end_date: datetime | None = None,
        reason: str | None = None,
        changed_by_user_id: UUID | None = None,
    ) -> MembershipFreeze:
        """
        Freeze a membership. Changes its status to 'FROZEN'.
        """
        if expected_end_date is not None and expected_end_date <= start_date:
            raise ValueError("expected_end_date must be after start_date")

        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")

        valid_from_statuses = {"ACTIVE", "PAST_DUE"}
        if membership.status not in valid_from_statuses:
            raise ValueError(
                f"Membership status '{membership.status}' cannot be frozen"
            )

        stmt = select(MembershipFreeze).where(
            MembershipFreeze.membership_id == membership_id,
            MembershipFreeze.actual_end_date.is_(None),
        )
        existing_freeze = await self.session.execute(stmt)
        if existing_freeze.scalar_one_or_none():
            raise ValueError("Membership already has an active freeze")

        freeze = MembershipFreeze(
            membership_id=membership_id,
            start_date=start_date,
            expected_end_date=expected_end_date,
            previous_status=membership.status,
            reason=reason,
            tenant_id=membership.tenant_id,
        )
        self.session.add(freeze)

        history = MembershipStatusHistory(
            membership_id=membership_id,
            old_status=membership.status,
            new_status="FROZEN",
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id,
        )
        self.session.add(history)

        membership.status = "FROZEN"

        try:
            await self.session.flush()
        except exc.IntegrityError:
            await self.session.rollback()
            raise ValueError("Membership already has an active freeze")

        return freeze

    async def unfreeze_membership(
        self,
        membership_id: UUID,
        changed_by_user_id: UUID | None = None,
    ) -> Membership:
        """
        Unfreeze a membership manually. Changes status back to previous status
        and updates the freeze record's actual_end_date.
        """
        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")

        if membership.status != "FROZEN":
            raise ValueError("Membership is not frozen")

        stmt = (
            select(MembershipFreeze)
            .where(
                MembershipFreeze.membership_id == membership_id,
                MembershipFreeze.actual_end_date.is_(None),
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        freeze = result.scalar_one_or_none()

        if not freeze:
            raise ValueError("No active freeze record found")

        now = datetime.now(UTC)
        freeze.actual_end_date = now

        if membership.end_date:
            delta = now - freeze.start_date
            membership.end_date += delta

        new_status = freeze.previous_status or "ACTIVE"

        history = MembershipStatusHistory(
            membership_id=membership_id,
            old_status="FROZEN",
            new_status=new_status,
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id,
        )
        self.session.add(history)

        membership.status = new_status
        await self.session.flush()
        return membership

    async def cancel_membership(
        self,
        membership_id: UUID,
        effective_date: datetime,
        reason: str | None,
        changed_by_user_id: UUID | None = None,
    ) -> MembershipCancellation:
        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")

        valid_from_statuses = {"ACTIVE", "FROZEN", "PAST_DUE", "SCHEDULED", "PENDING"}
        if membership.status not in valid_from_statuses:
            raise ValueError(
                f"Membership status '{membership.status}' cannot be cancelled"
            )

        now = datetime.now(UTC)

        cancellation = MembershipCancellation(
            membership_id=membership_id,
            cancelled_at=now,
            effective_date=effective_date,
            reason=reason,
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id,
        )
        self.session.add(cancellation)

        if effective_date > now:
            membership.scheduled_cancellation_at = effective_date
        else:
            if membership.status == "FROZEN":
                stmt = (
                    select(MembershipFreeze)
                    .where(
                        MembershipFreeze.membership_id == membership_id,
                        MembershipFreeze.actual_end_date.is_(None),
                    )
                    .with_for_update()
                )
                freeze = (await self.session.execute(stmt)).scalar_one_or_none()
                if freeze:
                    freeze.actual_end_date = now

            history = MembershipStatusHistory(
                membership_id=membership_id,
                old_status=membership.status,
                new_status="CANCELLED",
                changed_at=now,
                changed_by_user_id=changed_by_user_id,
                tenant_id=membership.tenant_id,
            )
            self.session.add(history)
            membership.status = "CANCELLED"
            membership.end_date = effective_date

        await self.session.flush()
        return cancellation

    async def renew_membership(
        self,
        membership_id: UUID,
        next_plan_version_id: UUID,
        renewal_date: datetime,
        changed_by_user_id: UUID | None = None,
    ) -> MembershipRenewal:
        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")

        valid_from_statuses = {"ACTIVE", "FROZEN", "PAST_DUE"}
        if membership.status not in valid_from_statuses:
            raise ValueError(
                f"Membership status '{membership.status}' cannot be renewed"
            )

        stmt = select(MembershipRenewal).where(
            MembershipRenewal.membership_id == membership_id,
            MembershipRenewal.renewal_date == renewal_date,
        )
        if (await self.session.execute(stmt)).scalar_one_or_none():
            raise ValueError("Membership renewal already processed for this date")

        pv_stmt = select(PlanVersion).where(PlanVersion.id == next_plan_version_id)
        pv = (await self.session.execute(pv_stmt)).scalar_one_or_none()
        if not pv or not pv.is_published:
            raise ValueError("Valid published next plan version not found")

        renewal = MembershipRenewal(
            membership_id=membership_id,
            next_plan_version_id=next_plan_version_id,
            renewal_date=renewal_date,
            price_snapshot=pv.price_amount_minor,
            price_snapshot_currency=pv.currency,
            terms_snapshot=pv.terms,
            status=RenewalStatus.APPLIED.value
            if renewal_date <= datetime.now(UTC)
            else RenewalStatus.PENDING.value,
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id,
        )
        self.session.add(renewal)

        now = datetime.now(UTC)
        if renewal_date <= now:
            membership.plan_version_id = next_plan_version_id
            membership.price_snapshot = pv.price_amount_minor
            membership.price_snapshot_currency = pv.currency
            membership.terms_snapshot = pv.terms

            if membership.end_date:
                # Close current active period if any
                stmt_active_period = select(MembershipPeriod).where(
                    MembershipPeriod.membership_id == membership.id,
                    MembershipPeriod.is_active,
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

            # Immediate renew: allocate/refresh entitlement wallets from new plan version
            from app.services.entitlement import EntitlementService

            await EntitlementService.grant_from_plan_version(
                self.session,
                membership,
                next_plan_version_id,
                actor_id=changed_by_user_id,
                reason="renewal_immediate",
            )

        await self.session.flush()
        return renewal

    async def activate_scheduled_membership(
        self,
        membership_id: UUID,
        changed_by_user_id: UUID | None = None,
    ) -> Membership:
        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")

        if membership.status != "SCHEDULED":
            raise ValueError(
                f"Membership status '{membership.status}' cannot be activated"
            )

        if membership.start_date > datetime.now(UTC):
            raise ValueError("Membership start date is in the future")

        membership.status = "ACTIVE"

        # Activate the period
        stmt_period = (
            select(MembershipPeriod)
            .where(
                MembershipPeriod.membership_id == membership.id,
                MembershipPeriod.is_active == False,
            )
            .order_by(MembershipPeriod.start_date.asc())
        )
        period = (await self.session.execute(stmt_period)).scalars().first()
        if period:
            period.is_active = True

        history = MembershipStatusHistory(
            membership_id=membership.id,
            old_status="SCHEDULED",
            new_status="ACTIVE",
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id,
        )
        self.session.add(history)

        from app.services.entitlement import EntitlementService

        await EntitlementService.grant_from_plan_version(
            self.session,
            membership,
            membership.plan_version_id,
            actor_id=changed_by_user_id,
            reason="activate",
        )

        await self.session.flush()

        return membership

    async def expire_membership(
        self,
        membership_id: UUID,
        changed_by_user_id: UUID | None = None,
    ) -> Membership:
        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")

        if membership.status not in ("ACTIVE", "PAST_DUE"):
            raise ValueError(
                f"Membership status '{membership.status}' cannot be expired"
            )

        stmt_period = select(MembershipPeriod).where(
            MembershipPeriod.membership_id == membership.id, MembershipPeriod.is_active
        )
        active_period = (await self.session.execute(stmt_period)).scalar_one_or_none()
        if active_period:
            active_period.is_active = False

        history = MembershipStatusHistory(
            membership_id=membership_id,
            old_status=membership.status,
            new_status="EXPIRED",
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id,
        )
        self.session.add(history)

        membership.status = "EXPIRED"

        await self.session.flush()
        return membership

    async def mark_past_due(
        self,
        membership_id: UUID,
        changed_by_user_id: UUID | None = None,
    ) -> Membership:
        membership = await self.get_membership(membership_id, for_update=True)
        if not membership:
            raise ValueError("Membership not found")

        if membership.status != "ACTIVE":
            raise ValueError(
                f"Membership status '{membership.status}' cannot be marked PAST_DUE"
            )

        history = MembershipStatusHistory(
            membership_id=membership_id,
            old_status=membership.status,
            new_status="PAST_DUE",
            changed_at=datetime.now(UTC),
            changed_by_user_id=changed_by_user_id,
            tenant_id=membership.tenant_id,
        )
        self.session.add(history)

        membership.status = "PAST_DUE"

        await self.session.flush()
        return membership
