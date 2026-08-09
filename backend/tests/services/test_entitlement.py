"""Phase 9 entitlement engine tests — real PostgreSQL, wallet/ledger, concurrency, RLS."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.entitlement import (
    EntitlementDefinition,
    EntitlementTransaction,
    EntitlementTransactionType,
    EntitlementType,
    EntitlementWallet,
    MembershipEntitlement,
    MembershipEntitlementStatus,
)
from app.models.member import Member
from app.models.membership import Membership, Plan, PlanVersion
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.entitlement import EntitlementService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def setup_tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Test Org", domain=f"test-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t_id = uuid4()
    tenant = Tenant(
        id=t_id,
        name="Test Tenant",
        organization_id=org.id,
        location_code=f"LOC-{t_id}",
    )
    db_session.add(tenant)
    await db_session.commit()
    return tenant


@pytest_asyncio.fixture
async def setup_tenant_b(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Other Org", domain=f"other-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t_id = uuid4()
    tenant = Tenant(
        id=t_id,
        name="Other Tenant",
        organization_id=org.id,
        location_code=f"LOC-{t_id}",
    )
    db_session.add(tenant)
    await db_session.commit()
    return tenant


async def _seed_membership_wallet(
    db: AsyncSession,
    tenant: Tenant,
    *,
    remaining: int = 1,
    ent_type: EntitlementType = EntitlementType.COUNT,
    code: str = "PT_SESSION",
) -> tuple[Member, Membership, EntitlementDefinition, EntitlementWallet]:
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"MEM-{uuid4().hex[:6]}",
        first_name="Test",
        last_name="Member",
        email=f"test-{uuid4()}@example.com",
    )
    db.add(member)
    await db.flush()

    plan = Plan(id=uuid4(), tenant_id=tenant.id, name="Plan", is_active=True)
    db.add(plan)
    await db.flush()
    pv = PlanVersion(
        id=uuid4(),
        tenant_id=tenant.id,
        plan_id=plan.id,
        version=1,
        price_amount_minor=10000,
        currency="TRY",
        billing_cycle_months=1,
        terms={},
        is_published=True,
        published_at=datetime.now(UTC),
    )
    db.add(pv)
    await db.flush()

    membership = Membership(
        id=uuid4(),
        tenant_id=tenant.id,
        member_id=member.id,
        plan_version_id=pv.id,
        status="ACTIVE",
        start_date=datetime.now(UTC) - timedelta(days=1),
        end_date=datetime.now(UTC) + timedelta(days=30),
        price_snapshot=10000,
        price_snapshot_currency="TRY",
        terms_snapshot={},
    )
    db.add(membership)
    await db.flush()

    ent_def = EntitlementDefinition(
        id=uuid4(),
        tenant_id=tenant.id,
        code=code,
        name=code,
        type=ent_type,
        is_active=True,
    )
    db.add(ent_def)
    await db.flush()

    me = MembershipEntitlement(
        id=uuid4(),
        tenant_id=tenant.id,
        membership_id=membership.id,
        entitlement_id=ent_def.id,
        source_plan_version_id=pv.id,
        granted_quantity=remaining if ent_type == EntitlementType.COUNT else 1,
        unlimited=False,
        status=MembershipEntitlementStatus.ACTIVE.value,
    )
    db.add(me)
    await db.flush()

    wallet = EntitlementWallet(
        id=uuid4(),
        tenant_id=tenant.id,
        member_id=member.id,
        membership_id=membership.id,
        membership_entitlement_id=me.id,
        entitlement_id=ent_def.id,
        allocated=remaining if ent_type == EntitlementType.COUNT else 1,
        reserved=0,
        consumed=0,
        remaining=remaining if ent_type == EntitlementType.COUNT else 1,
    )
    db.add(wallet)
    await db.commit()
    return member, membership, ent_def, wallet


@pytest.mark.asyncio
async def test_entitlement_zero_balance(db_session, setup_tenant):
    member, _, _, _ = await _seed_membership_wallet(
        db_session, setup_tenant, remaining=0
    )
    res = await EntitlementService.consume_access(
        db_session, setup_tenant.id, member.id, "PT_SESSION", "idem-zero"
    )
    await db_session.commit()
    assert res["granted"] is False
    assert res["reason"] == "ZERO_BALANCE"


@pytest.mark.asyncio
async def test_entitlement_check_no_mutation(db_session, setup_tenant):
    member, _, _, wallet = await _seed_membership_wallet(
        db_session, setup_tenant, remaining=3
    )
    res = await EntitlementService.check_access(
        db_session, setup_tenant.id, member.id, "PT_SESSION", 1
    )
    assert res["granted"] is True
    assert res["remaining"] == 3

    await db_session.refresh(wallet)
    assert wallet.remaining == 3


@pytest.mark.asyncio
async def test_entitlement_consume_success(db_session, setup_tenant):
    member, membership, ent_def, wallet = await _seed_membership_wallet(
        db_session, setup_tenant, remaining=2
    )
    res = await EntitlementService.consume_access(
        db_session, setup_tenant.id, member.id, "PT_SESSION", "idem-ok"
    )
    await db_session.commit()
    assert res["granted"] is True
    assert res["remaining"] == 1

    await db_session.refresh(wallet)
    assert wallet.remaining == 1
    assert wallet.consumed == 1

    txs = (
        await db_session.execute(
            select(EntitlementTransaction).where(
                EntitlementTransaction.tenant_id == setup_tenant.id,
                EntitlementTransaction.idempotency_key == "idem-ok",
            )
        )
    ).scalars().all()
    assert len(txs) == 1
    assert txs[0].transaction_type == EntitlementTransactionType.CONSUME.value
    assert txs[0].membership_id == membership.id
    assert txs[0].entitlement_id == ent_def.id


@pytest.mark.asyncio
async def test_entitlement_idempotent_replay(db_session, setup_tenant):
    member, _, _, wallet = await _seed_membership_wallet(
        db_session, setup_tenant, remaining=2
    )
    r1 = await EntitlementService.consume_access(
        db_session, setup_tenant.id, member.id, "PT_SESSION", "same-key"
    )
    await db_session.commit()
    r2 = await EntitlementService.consume_access(
        db_session, setup_tenant.id, member.id, "PT_SESSION", "same-key"
    )
    await db_session.commit()
    assert r1["granted"] is True
    assert r2["granted"] is True
    assert r2["reason"] == "IDEMPOTENT"

    await db_session.refresh(wallet)
    assert wallet.remaining == 1
    assert wallet.consumed == 1

    count = (
        await db_session.execute(
            select(EntitlementTransaction).where(
                EntitlementTransaction.tenant_id == setup_tenant.id,
                EntitlementTransaction.idempotency_key == "same-key",
            )
        )
    ).scalars().all()
    assert len(count) == 1


@pytest.mark.asyncio
async def test_entitlement_concurrent_double_consume(pg_engine, setup_tenant, db_session):
    """Two separate DB sessions compete for remaining=1."""
    member, _, _, _ = await _seed_membership_wallet(
        db_session, setup_tenant, remaining=1
    )
    member_id = member.id
    tenant_id = setup_tenant.id

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)

    async def consume(key: str) -> dict:
        async with maker() as session:
            res = await EntitlementService.consume_access(
                session, tenant_id, member_id, "PT_SESSION", key
            )
            await session.commit()
            return res

    import asyncio

    res1, res2 = await asyncio.gather(consume("c-a"), consume("c-b"))
    successes = sum(1 for r in (res1, res2) if r["granted"])
    assert successes == 1

    async with maker() as session:
        wallet = (
            await session.execute(
                select(EntitlementWallet).where(
                    EntitlementWallet.tenant_id == tenant_id,
                    EntitlementWallet.member_id == member_id,
                )
            )
        ).scalars().first()
        assert wallet is not None
        assert wallet.remaining == 0
        assert wallet.consumed == 1

        txs = (
            await session.execute(
                select(EntitlementTransaction).where(
                    EntitlementTransaction.tenant_id == tenant_id,
                    EntitlementTransaction.transaction_type
                    == EntitlementTransactionType.CONSUME.value,
                )
            )
        ).scalars().all()
        assert len(txs) == 1


@pytest.mark.asyncio
async def test_boolean_entitlement_grant(db_session, setup_tenant):
    member, _, _, _ = await _seed_membership_wallet(
        db_session,
        setup_tenant,
        remaining=1,
        ent_type=EntitlementType.BOOLEAN,
        code="GYM_ACCESS",
    )
    check = await EntitlementService.check_access(
        db_session, setup_tenant.id, member.id, "GYM_ACCESS"
    )
    assert check["granted"] is True

    res = await EntitlementService.consume_access(
        db_session, setup_tenant.id, member.id, "GYM_ACCESS", "bool-1"
    )
    await db_session.commit()
    assert res["granted"] is True
    # BOOLEAN does not decrement remaining
    assert res["remaining"] == 1


@pytest.mark.asyncio
async def test_no_active_membership_denied(db_session, setup_tenant):
    member = Member(
        id=uuid4(),
        tenant_id=setup_tenant.id,
        member_number=f"MEM-{uuid4().hex[:6]}",
        first_name="No",
        last_name="Membership",
        email=f"nomem-{uuid4()}@example.com",
    )
    db_session.add(member)
    def_id = uuid4()
    db_session.add(
        EntitlementDefinition(
            id=def_id,
            tenant_id=setup_tenant.id,
            code="PT_SESSION",
            name="PT",
            type=EntitlementType.COUNT,
        )
    )
    await db_session.commit()

    res = await EntitlementService.consume_access(
        db_session, setup_tenant.id, member.id, "PT_SESSION", "no-mem"
    )
    await db_session.commit()
    assert res["granted"] is False
    assert res["reason"] == "NO_ACTIVE_MEMBERSHIP"


@pytest.mark.asyncio
async def test_tenant_rls_isolation_wallets(
    pg_engine, pg_session_maker, db_session, setup_tenant, setup_tenant_b
):
    """app_user with SET LOCAL cannot read other tenant wallets."""
    member_a, _, _, wallet_a = await _seed_membership_wallet(
        db_session, setup_tenant, remaining=5, code="PT_A"
    )
    await _seed_membership_wallet(
        db_session, setup_tenant_b, remaining=9, code="PT_B"
    )

    async with pg_session_maker() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(setup_tenant.id)},
        )
        rows = (
            await session.execute(select(EntitlementWallet))
        ).scalars().all()
        # Only tenant A wallets visible under RLS
        assert all(w.tenant_id == setup_tenant.id for w in rows)
        assert any(w.id == wallet_a.id for w in rows)
        assert all(w.tenant_id != setup_tenant_b.id for w in rows)

        # Spoof insert with tenant B should fail WITH CHECK
        bad = EntitlementWallet(
            id=uuid4(),
            tenant_id=setup_tenant_b.id,
            member_id=member_a.id,
            membership_id=uuid4(),
            membership_entitlement_id=uuid4(),
            entitlement_id=uuid4(),
            allocated=1,
            reserved=0,
            consumed=0,
            remaining=1,
        )
        session.add(bad)
        with pytest.raises((DBAPIError, IntegrityError)):
            await session.commit()
        await session.rollback()


def test_permission_allow_deny_matrix():
    from app.core.authorization import AuthorizationService, DefaultRole
    from app.models.rbac import Permission, Role, UserRole
    from app.models.user import User

    tenant_id = uuid4()
    consume_perm = Permission(id=uuid4(), name="entitlements:consume")
    check_perm = Permission(id=uuid4(), name="entitlements:check")

    front_desk = Role(
        id=uuid4(),
        name=DefaultRole.FRONT_DESK.value,
        permissions=[consume_perm, check_perm],
    )
    trainer = Role(
        id=uuid4(),
        name=DefaultRole.TRAINER.value,
        permissions=[check_perm],
    )

    user_fd = User(id=uuid4(), email="fd@test.com", is_superuser=False)
    user_fd.user_roles = [
        UserRole(
            id=uuid4(),
            user_id=user_fd.id,
            role_id=front_desk.id,
            tenant_id=tenant_id,
            role=front_desk,
        )
    ]

    user_tr = User(id=uuid4(), email="tr@test.com", is_superuser=False)
    user_tr.user_roles = [
        UserRole(
            id=uuid4(),
            user_id=user_tr.id,
            role_id=trainer.id,
            tenant_id=tenant_id,
            role=trainer,
        )
    ]

    assert AuthorizationService.is_authorized(
        user=user_fd, permission="entitlements:consume", resource_tenant_id=tenant_id
    )
    assert AuthorizationService.is_authorized(
        user=user_fd, permission="entitlements:check", resource_tenant_id=tenant_id
    )
    assert not AuthorizationService.is_authorized(
        user=user_tr, permission="entitlements:consume", resource_tenant_id=tenant_id
    )
    assert AuthorizationService.is_authorized(
        user=user_tr, permission="entitlements:check", resource_tenant_id=tenant_id
    )
