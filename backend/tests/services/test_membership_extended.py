from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.api.deps import current_tenant_id_var
from app.models.member import Member
from app.models.membership import (
    MembershipFreeze,
    Plan,
    PlanVersion,
)
from app.services.membership import MembershipService


@pytest.fixture
async def setup_data(pg_session_maker):
    tenant_id = uuid4()
    token = current_tenant_id_var.set(tenant_id)

    async with pg_session_maker() as session:
        member = Member(
            tenant_id=tenant_id,
            member_number="M-TEST1",
            first_name="T1",
            last_name="T1",
            status="ACTIVE",
        )
        session.add(member)
        plan = Plan(tenant_id=tenant_id, name="Test Plan")
        session.add(plan)
        await session.flush()

        pv1 = PlanVersion(
            tenant_id=tenant_id,
            plan_id=plan.id,
            version=1,
            price_amount_minor=10000,
            billing_cycle_months=1,
            is_published=True,
        )
        pv2 = PlanVersion(
            tenant_id=tenant_id,
            plan_id=plan.id,
            version=2,
            price_amount_minor=12000,
            billing_cycle_months=1,
            is_published=True,
        )
        session.add_all([pv1, pv2])
        await session.commit()

        # Save IDs to return
        member_id = member.id
        pv1_id = pv1.id
        pv2_id = pv2.id

    yield tenant_id, member_id, pv1_id, pv2_id
    current_tenant_id_var.reset(token)


@pytest.mark.asyncio
async def test_start_and_overlap(pg_session_maker, setup_data):
    tenant_id, member_id, pv1_id, _ = setup_data
    current_tenant_id_var.set(tenant_id)
    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        # Should succeed
        m1 = await service.start_membership(member_id, pv1_id, now, tenant_id)
        assert m1.status == "ACTIVE"
        from sqlalchemy import select as sa_select

        from app.core.event_types import MEMBERSHIP_ACTIVATED_V1
        from app.models.outbox import OutboxEvent

        events = list(
            (
                await session.execute(
                    sa_select(OutboxEvent).where(
                        OutboxEvent.tenant_id == tenant_id,
                        OutboxEvent.event_type == MEMBERSHIP_ACTIVATED_V1,
                    )
                )
            ).scalars()
        )
        assert len(events) == 1
        assert str(m1.id) in str(events[0].payload)
        await session.commit()

    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        # Should fail with overlap
        with pytest.raises(
            ValueError, match="already has an active or scheduled membership"
        ):
            await service.start_membership(member_id, pv1_id, now, tenant_id)


@pytest.mark.asyncio
async def test_past_due_freeze_restore(pg_session_maker, setup_data):
    tenant_id, member_id, pv1_id, _ = setup_data
    current_tenant_id_var.set(tenant_id)
    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        m = await service.start_membership(member_id, pv1_id, now, tenant_id)
        await session.commit()
        membership_id = m.id

    async with pg_session_maker() as session:
        service = MembershipService(session)
        await service.mark_past_due(membership_id)
        await session.commit()

    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        freeze_end = now + timedelta(days=5)
        await service.freeze_membership(membership_id, now, freeze_end, "Wait")
        await session.commit()

    async with pg_session_maker() as session:
        service = MembershipService(session)
        m = await service.unfreeze_membership(membership_id)
        assert m.status == "PAST_DUE"
        await session.commit()


@pytest.mark.asyncio
async def test_frozen_cancel(pg_session_maker, setup_data):
    tenant_id, member_id, pv1_id, _ = setup_data
    current_tenant_id_var.set(tenant_id)

    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        m = await service.start_membership(member_id, pv1_id, now, tenant_id)
        await session.commit()
        membership_id = m.id

    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        freeze_end = now + timedelta(days=5)
        await service.freeze_membership(membership_id, now, freeze_end, "Wait")
        await session.commit()

    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        await service.cancel_membership(membership_id, now, "Cancel while frozen")
        m = await service.get_membership(membership_id)
        assert m.status == "CANCELLED"
        # Verify freeze actual_end_date is set
        from sqlalchemy import select

        stmt = select(MembershipFreeze).where(
            MembershipFreeze.membership_id == membership_id
        )
        freeze = (await session.execute(stmt)).scalars().first()
        assert freeze.actual_end_date is not None
        await session.commit()


@pytest.mark.asyncio
async def test_renew_different_plan(pg_session_maker, setup_data):
    tenant_id, member_id, pv1_id, pv2_id = setup_data
    current_tenant_id_var.set(tenant_id)

    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        m = await service.start_membership(member_id, pv1_id, now, tenant_id)
        await session.commit()
        membership_id = m.id

    async with pg_session_maker() as session:
        service = MembershipService(session)
        now = datetime.now(UTC)
        await service.renew_membership(membership_id, pv2_id, now)
        m = await service.get_membership(membership_id)
        assert m.plan_version_id == pv2_id

        # Test duplicate renewal fails
        with pytest.raises(ValueError, match="already processed"):
            await service.renew_membership(membership_id, pv2_id, now)
        await session.commit()
