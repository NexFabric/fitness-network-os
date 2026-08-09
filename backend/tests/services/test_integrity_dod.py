"""Phase 15.5B DoD evidence: finance/entitlement immutability + RBAC + envelope."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
import yaml
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.authorization import AuthorizationService
from app.core.events import EnvelopeValidationError, validate_envelope
from app.models.entitlement import (
    EntitlementDefinition,
    EntitlementTransaction,
    EntitlementTransactionType,
    EntitlementType,
    EntitlementWallet,
    MembershipEntitlement,
    MembershipEntitlementStatus,
)
from app.models.finance import PaymentAllocation, PaymentAllocationReversal
from app.models.member import Member
from app.models.membership import Membership, Plan, PlanVersion
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.services.finance import FinanceService
from app.services.outbox import OutboxService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="DoD Org", domain=f"dod-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="DoD T",
        organization_id=org.id,
        location_code=f"D-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


def test_member_yaml_least_privilege():
    data = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / "permissions.yml").read_text()
    )
    member_perms = set(data["roles"]["MEMBER"]["permissions"])
    assert "members:read" not in member_perms
    assert "access:issue" not in member_perms
    assert "access:issue:self" in member_perms
    assert "entitlements:check" not in member_perms
    assert "entitlements:check:self" in member_perms
    for role in ("GYM_OWNER", "GYM_ADMIN", "GYM_MANAGER"):
        role_perms = set(data["roles"][role]["permissions"])
        assert "outbox:dispatch" not in role_perms
        assert "outbox:write" not in role_perms
        assert "inbox:write" not in role_perms


def test_member_not_authorized_members_read():
    tid = uuid4()
    user = User(id=uuid4(), email=f"m-{uuid4()}@t.com", hashed_password="x")
    role = Role(id=uuid4(), name="MEMBER")
    perm = Permission(id=uuid4(), name="profile:read")
    role.permissions = [perm]
    ur = UserRole(id=uuid4(), user_id=user.id, role_id=role.id, tenant_id=tid)
    ur.role = role
    user.user_roles = [ur]
    assert not AuthorizationService.is_authorized(
        user=user, permission="members:read", resource_tenant_id=tid
    )
    assert not AuthorizationService.is_authorized(
        user=user, permission="access:issue", resource_tenant_id=tid
    )


def test_envelope_mismatch_rejected():
    tid = uuid4()
    env = {
        "specversion": "1.0",
        "id": "x",
        "source": "s",
        "type": "payment.received.v1",
        "time": "t",
        "tenantid": str(uuid4()),
        "data": {},
    }
    with pytest.raises(EnvelopeValidationError, match="tenantid_mismatch"):
        validate_envelope(env, tenant_id=tid, event_type="payment.received.v1")
    env["tenantid"] = str(tid)
    with pytest.raises(EnvelopeValidationError, match="type_mismatch"):
        validate_envelope(env, tenant_id=tid, event_type="other.event.v1")


@pytest.mark.asyncio
async def test_enqueue_rejects_bad_envelope(db_session, tenant):
    svc = OutboxService(db_session)
    bad = {
        "specversion": "1.0",
        "id": "1",
        "source": "s",
        "type": "test.event.v1",
        "time": "t",
        "tenantid": str(uuid4()),
        "data": {},
    }
    with pytest.raises(EnvelopeValidationError, match="tenantid_mismatch"):
        await svc.enqueue(tenant.id, "test.event.v1", bad, wrap_envelope=True)
    await db_session.rollback()


@pytest.mark.asyncio
async def test_enqueue_rejects_unversioned_event_type(db_session, tenant):
    from app.core.event_types import EventTypeValidationError

    svc = OutboxService(db_session)
    with pytest.raises(EventTypeValidationError):
        await svc.enqueue(tenant.id, "membership.renewed", {"m": "1"})
    await db_session.rollback()


@pytest.mark.asyncio
async def test_finance_allocation_update_denied(db_session, tenant):
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"M-{uuid4().hex[:6]}",
        first_name="A",
        last_name="B",
    )
    db_session.add(member)
    await db_session.flush()
    fin = FinanceService(db_session)
    ba = await fin.get_or_create_billing_account(
        tenant.id, member_id=member.id, currency="TRY"
    )
    inv = await fin.create_invoice(
        tenant.id,
        ba.id,
        items=[{"description": "x", "quantity": 1, "unit_amount_minor": 1000}],
        issue=True,
    )
    pay = await fin.record_payment(
        tenant.id,
        ba.id,
        amount_minor=1000,
        method="CASH",
        currency="TRY",
        allocations=[{"invoice_id": inv.id, "amount_minor": 1000}],
        idempotency_key=f"pay-{uuid4().hex}",
    )
    payment_id = pay.id
    await db_session.commit()
    alloc_id = (
        await db_session.execute(
            select(PaymentAllocation.id).where(
                PaymentAllocation.payment_id == payment_id
            )
        )
    ).scalar_one()

    denied = False
    try:
        await db_session.execute(
            text("UPDATE payment_allocations SET amount_minor = 1 WHERE id = :id"),
            {"id": alloc_id},
        )
    except Exception:
        denied = True
        await db_session.rollback()
    assert denied


@pytest.mark.asyncio
async def test_finance_reversal_delete_denied(db_session, tenant):
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"M-{uuid4().hex[:6]}",
        first_name="A",
        last_name="B",
    )
    db_session.add(member)
    await db_session.flush()
    fin = FinanceService(db_session)
    ba = await fin.get_or_create_billing_account(
        tenant.id, member_id=member.id, currency="TRY"
    )
    inv = await fin.create_invoice(
        tenant.id,
        ba.id,
        items=[{"description": "x", "quantity": 1, "unit_amount_minor": 1000}],
        issue=True,
    )
    pay = await fin.record_payment(
        tenant.id,
        ba.id,
        amount_minor=1000,
        method="CASH",
        currency="TRY",
        allocations=[{"invoice_id": inv.id, "amount_minor": 1000}],
        idempotency_key=f"pay-{uuid4().hex}",
    )
    payment_id = pay.id
    await fin.refund_payment(
        tenant.id,
        payment_id,
        amount_minor=400,
        idempotency_key=f"r-{uuid4().hex}",
    )
    await db_session.commit()
    rev_id = (
        await db_session.execute(
            select(PaymentAllocationReversal.id).where(
                PaymentAllocationReversal.tenant_id == tenant.id
            )
        )
    ).scalar_one()

    denied = False
    try:
        await db_session.execute(
            text("DELETE FROM payment_allocation_reversals WHERE id = :id"),
            {"id": rev_id},
        )
    except Exception:
        denied = True
        await db_session.rollback()
    assert denied


@pytest.mark.asyncio
async def test_entitlement_ledger_append_only_and_wallet_restrict(db_session, tenant):
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"E-{uuid4().hex[:6]}",
        first_name="E",
        last_name="N",
    )
    db_session.add(member)
    await db_session.flush()
    plan = Plan(id=uuid4(), tenant_id=tenant.id, name="P", is_active=True)
    db_session.add(plan)
    await db_session.flush()
    pv = PlanVersion(
        id=uuid4(),
        tenant_id=tenant.id,
        plan_id=plan.id,
        version=1,
        price_amount_minor=1000,
        currency="TRY",
        billing_cycle_months=1,
        terms={},
        is_published=True,
        published_at=datetime.now(UTC),
    )
    db_session.add(pv)
    await db_session.flush()
    membership = Membership(
        id=uuid4(),
        tenant_id=tenant.id,
        member_id=member.id,
        plan_version_id=pv.id,
        status="ACTIVE",
        start_date=datetime.now(UTC) - timedelta(days=1),
        end_date=datetime.now(UTC) + timedelta(days=30),
        price_snapshot=1000,
        price_snapshot_currency="TRY",
        terms_snapshot={},
    )
    db_session.add(membership)
    await db_session.flush()
    ent = EntitlementDefinition(
        id=uuid4(),
        tenant_id=tenant.id,
        code=f"PT-{uuid4().hex[:4]}",
        name="PT",
        type=EntitlementType.COUNT,
        is_active=True,
    )
    db_session.add(ent)
    await db_session.flush()
    me = MembershipEntitlement(
        id=uuid4(),
        tenant_id=tenant.id,
        membership_id=membership.id,
        entitlement_id=ent.id,
        source_plan_version_id=pv.id,
        granted_quantity=5,
        unlimited=False,
        status=MembershipEntitlementStatus.ACTIVE.value,
    )
    db_session.add(me)
    await db_session.flush()
    wallet = EntitlementWallet(
        id=uuid4(),
        tenant_id=tenant.id,
        member_id=member.id,
        membership_id=membership.id,
        membership_entitlement_id=me.id,
        entitlement_id=ent.id,
        allocated=5,
        reserved=0,
        consumed=0,
        remaining=5,
    )
    db_session.add(wallet)
    await db_session.flush()
    tx_id = uuid4()
    wallet_id = wallet.id
    db_session.add(
        EntitlementTransaction(
            id=tx_id,
            tenant_id=tenant.id,
            wallet_id=wallet_id,
            membership_id=membership.id,
            entitlement_id=ent.id,
            transaction_type=EntitlementTransactionType.ALLOCATE.value,
            quantity=5,
            balance_before=0,
            balance_after=5,
            idempotency_key=f"idem-{uuid4().hex}",
        )
    )
    await db_session.commit()

    denied_u = False
    try:
        await db_session.execute(
            text("UPDATE entitlement_transactions SET quantity = 0 WHERE id = :id"),
            {"id": tx_id},
        )
    except Exception:
        denied_u = True
        await db_session.rollback()
    assert denied_u

    denied_d = False
    try:
        await db_session.execute(
            text("DELETE FROM entitlement_transactions WHERE id = :id"),
            {"id": tx_id},
        )
    except Exception:
        denied_d = True
        await db_session.rollback()
    assert denied_d

    denied_w = False
    try:
        await db_session.execute(
            text("DELETE FROM entitlement_wallets WHERE id = :id"),
            {"id": wallet_id},
        )
    except Exception:
        denied_w = True
        await db_session.rollback()
    assert denied_w


def test_permissions_db_rejects_extra_grant_mutation(pg_engine):
    """Depends on pg_engine so alembic head is applied to the test DB."""
    import os
    import subprocess
    import sys

    from sqlalchemy import create_engine
    from sqlalchemy import text as sql_text

    url = os.environ.get("TEST_DATABASE_URL", "").replace("+asyncpg", "+psycopg")
    if not url:
        pytest.skip("no TEST_DATABASE_URL")
    try:
        eng = create_engine(url)
        with eng.connect() as c:
            c.execute(sql_text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"sync engine unavailable: {e}")

    with eng.begin() as conn:
        row = conn.execute(
            sql_text(
                """
                SELECT r.id, p.id
                FROM roles r, permissions p
                WHERE r.name = 'GYM_MANAGER' AND p.name = 'outbox:dispatch'
                """
            )
        ).fetchone()
        if not row:
            pytest.skip("seed missing")
        role_id, perm_id = row
        conn.execute(
            sql_text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT CAST(:r AS uuid), CAST(:p AS uuid)
                WHERE NOT EXISTS (
                  SELECT 1 FROM role_permissions
                  WHERE role_id = CAST(:r AS uuid) AND permission_id = CAST(:p AS uuid)
                )
                """
            ),
            {"r": str(role_id), "p": str(perm_id)},
        )

    script = Path(__file__).resolve().parents[2] / "scripts" / "check_permissions_db.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(Path(__file__).resolve().parents[2]),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )
    with eng.begin() as conn:
        conn.execute(
            sql_text(
                """
                DELETE FROM role_permissions
                WHERE role_id = CAST(:r AS uuid) AND permission_id = CAST(:p AS uuid)
                """
            ),
            {"r": str(role_id), "p": str(perm_id)},
        )
    eng.dispose()
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "extra DB grants" in (proc.stdout + proc.stderr)
