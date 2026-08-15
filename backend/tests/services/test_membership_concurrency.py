import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.membership import Membership, Plan, PlanVersion
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.membership import MembershipService


@pytest.fixture
async def setup_membership(pg_engine):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(
        pg_engine, class_=AsyncSession, expire_on_commit=False
    )

    tenant_id = uuid4()

    async with async_session() as db:
        org = Organization(name="Test Org", domain=f"test-{uuid4()}.com")
        db.add(org)
        await db.flush()

        tenant = Tenant(
            id=tenant_id,
            name="Tenant A",
            location_code=f"TA-{uuid4().hex[:6]}",
            organization_id=org.id,
        )
        db.add(tenant)
        await db.flush()

        member = Member(
            tenant_id=tenant_id,
            member_number="M-1",
            first_name="Test",
            last_name="Member",
            status="ACTIVE",
        )
        db.add(member)
        await db.flush()

        plan = Plan(tenant_id=tenant_id, name="Plan 1")
        db.add(plan)
        await db.flush()

        pv = PlanVersion(
            tenant_id=tenant_id,
            plan_id=plan.id,
            version=1,
            price_amount_minor=1000,
            billing_cycle_months=1,
            is_published=True,
        )
        db.add(pv)
        await db.flush()

        membership = Membership(
            tenant_id=tenant_id,
            member_id=member.id,
            plan_version_id=pv.id,
            status="ACTIVE",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(membership)
        await db.commit()

        return {"tenant_id": tenant_id, "membership_id": membership.id}


@pytest.mark.asyncio
async def test_concurrent_freeze(pg_session_maker, setup_membership):
    # Setup two concurrent operations
    async def freeze_op():
        async with pg_session_maker() as db:
            # RLS setup mock (normally done by middleware/dependency)
            await db.execute(
                text(
                    f"SET LOCAL app.current_tenant_id = '{setup_membership['tenant_id']}'"
                )
            )

            svc = MembershipService(db)
            start = datetime.now(UTC)
            end = start + timedelta(days=30)

            freeze = await svc.freeze_membership(
                membership_id=setup_membership["membership_id"],
                start_date=start,
                expected_end_date=end,
                reason="Concurrent freeze",
            )
            await db.commit()
            return freeze

    # Run them concurrently
    results = await asyncio.gather(freeze_op(), freeze_op(), return_exceptions=True)

    # Exactly one should succeed, one should fail (either deadlock rollback or ValueError from our check)
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1

    # Check that failure is due to either validation or concurrency
    # We expect a ValueError because the second one will get the lock, see it's frozen, and reject
    if isinstance(failures[0], ValueError):
        assert "cannot be frozen" in str(
            failures[0]
        ) or "already has an active freeze" in str(failures[0])


@pytest.mark.asyncio
async def test_concurrent_unfreeze(pg_session_maker, setup_membership):
    # First, intentionally freeze the membership so we can test concurrent unfreeze
    async with pg_session_maker() as db:
        await db.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_membership['tenant_id']}'")
        )
        svc = MembershipService(db)
        start = datetime.now(UTC)
        end = start + timedelta(days=30)
        await svc.freeze_membership(
            membership_id=setup_membership["membership_id"],
            start_date=start,
            expected_end_date=end,
            reason="Initial freeze",
        )
        await db.commit()

    async def unfreeze_op():
        async with pg_session_maker() as db:
            await db.execute(
                text(
                    f"SET LOCAL app.current_tenant_id = '{setup_membership['tenant_id']}'"
                )
            )
            svc = MembershipService(db)
            membership = await svc.unfreeze_membership(
                membership_id=setup_membership["membership_id"]
            )
            await db.commit()
            return membership

    results = await asyncio.gather(unfreeze_op(), unfreeze_op(), return_exceptions=True)

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1

    if isinstance(failures[0], ValueError):
        assert "not frozen" in str(
            failures[0]
        ) or "No active freeze record found" in str(failures[0])
