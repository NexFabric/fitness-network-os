"""Phase 13 QR access engine — real PostgreSQL tests."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.access import (
    AccessAttempt,
    AccessStatus,
    KeyStatus,
    QrJtiReplay,
    SigningKey,
)
from app.models.entitlement import (
    EntitlementDefinition,
    EntitlementType,
    EntitlementWallet,
    MembershipEntitlement,
    MembershipEntitlementStatus,
)
from app.models.location import Location
from app.models.member import Member
from app.models.membership import Membership, Plan, PlanVersion
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.models.user import User
from app.services.access import AccessService
from app.services.member import MemberService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="QR Org", domain=f"qr-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="QR Tenant",
        organization_id=org.id,
        location_code=f"LOC-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


async def _seed_member_with_entry(
    db: AsyncSession, tenant: Tenant
) -> tuple[Member, Location]:
    loc = Location(tenant_id=tenant.id, name="Main", timezone="UTC")
    db.add(loc)
    await db.flush()

    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"M-{uuid4().hex[:6]}",
        first_name="QR",
        last_name="User",
        email=f"qr-{uuid4()}@example.com",
    )
    db.add(member)
    await db.flush()

    plan = Plan(id=uuid4(), tenant_id=tenant.id, name="Access Plan", is_active=True)
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

    ent = EntitlementDefinition(
        id=uuid4(),
        tenant_id=tenant.id,
        code="GYM_ENTRY",
        name="Gym Entry",
        type=EntitlementType.BOOLEAN,
        is_active=True,
    )
    db.add(ent)
    await db.flush()

    me = MembershipEntitlement(
        id=uuid4(),
        tenant_id=tenant.id,
        membership_id=membership.id,
        entitlement_id=ent.id,
        source_plan_version_id=pv.id,
        granted_quantity=1,
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
        entitlement_id=ent.id,
        allocated=1,
        reserved=0,
        remaining=1,
        consumed=0,
    )
    db.add(wallet)
    await db.commit()
    return member, loc


@pytest.mark.asyncio
async def test_issue_and_validate_grant(db_session, tenant):
    member, loc = await _seed_member_with_entry(db_session, tenant)
    svc = AccessService(db_session)
    issued = await svc.issue_qr_token(tenant.id, member.id, ttl_seconds=60)
    await db_session.commit()

    assert issued.token.count(".") == 1
    assert issued.jti
    assert issued.kid

    result = await svc.validate_qr(
        tenant.id,
        issued.token,
        location_id=loc.id,
        action="GYM_ENTRY",
    )
    await db_session.commit()
    assert result.granted is True
    assert result.member_id == member.id
    assert result.checkin_id is not None

    attempts = (
        (
            await db_session.execute(
                select(AccessAttempt).where(AccessAttempt.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(attempts) == 1
    assert attempts[0].status == AccessStatus.GRANTED
    assert attempts[0].jti == issued.jti


@pytest.mark.asyncio
async def test_replay_denied(db_session, tenant):
    member, loc = await _seed_member_with_entry(db_session, tenant)
    svc = AccessService(db_session)
    issued = await svc.issue_qr_token(tenant.id, member.id)
    await db_session.commit()

    first = await svc.validate_qr(tenant.id, issued.token, location_id=loc.id)
    await db_session.commit()
    assert first.granted is True

    second = await svc.validate_qr(tenant.id, issued.token, location_id=loc.id)
    await db_session.commit()
    assert second.granted is False
    assert second.reason == "replay"

    replays = (
        (
            await db_session.execute(
                select(QrJtiReplay).where(QrJtiReplay.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(replays) == 1


@pytest.mark.asyncio
async def test_expired_token_denied(db_session, tenant):
    member, _ = await _seed_member_with_entry(db_session, tenant)
    svc = AccessService(db_session)
    past = datetime.now(UTC) - timedelta(seconds=120)
    issued = await svc.issue_qr_token(tenant.id, member.id, ttl_seconds=30, now=past)
    await db_session.commit()

    result = await svc.validate_qr(tenant.id, issued.token)
    await db_session.commit()
    assert result.granted is False
    assert result.reason == "token_expired"


@pytest.mark.asyncio
async def test_key_rotation_verify_only_still_works(db_session, tenant):
    member, loc = await _seed_member_with_entry(db_session, tenant)
    svc = AccessService(db_session)
    issued = await svc.issue_qr_token(tenant.id, member.id)
    await db_session.commit()

    new_key = await svc.rotate_signing_key(tenant.id)
    await db_session.commit()
    assert new_key.status == KeyStatus.ACTIVE

    keys = await svc.list_keys(tenant.id)
    statuses = {k.kid: k.status for k in keys}
    assert statuses[issued.kid] == KeyStatus.VERIFY_ONLY
    assert statuses[new_key.kid] == KeyStatus.ACTIVE

    # Old token still validates under VERIFY_ONLY
    result = await svc.validate_qr(tenant.id, issued.token, location_id=loc.id)
    await db_session.commit()
    assert result.granted is True


@pytest.mark.asyncio
async def test_revoked_key_denied(db_session, tenant):
    member, _ = await _seed_member_with_entry(db_session, tenant)
    svc = AccessService(db_session)
    issued = await svc.issue_qr_token(tenant.id, member.id)
    await db_session.commit()

    await svc.revoke_key(tenant.id, issued.kid)
    await db_session.commit()

    result = await svc.validate_qr(tenant.id, issued.token)
    await db_session.commit()
    assert result.granted is False
    assert result.reason == "key_revoked"


@pytest.mark.asyncio
async def test_cross_tenant_key_unknown(db_session, tenant):
    member, _ = await _seed_member_with_entry(db_session, tenant)
    svc = AccessService(db_session)
    issued = await svc.issue_qr_token(tenant.id, member.id)
    await db_session.commit()

    org = Organization(name="Other", domain=f"o-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    other = Tenant(
        id=uuid4(),
        name="Other",
        organization_id=org.id,
        location_code=f"X-{uuid4().hex[:4]}",
    )
    db_session.add(other)
    await db_session.commit()

    result = await svc.validate_qr(other.id, issued.token)
    await db_session.commit()
    assert result.granted is False
    assert result.reason in ("unknown_kid", "tenant_mismatch")


@pytest.mark.asyncio
async def test_no_entitlement_denied(db_session, tenant):
    loc = Location(tenant_id=tenant.id, name="Gate", timezone="UTC")
    db_session.add(loc)
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"N-{uuid4().hex[:6]}",
        first_name="No",
        last_name="Ent",
        email=f"no-{uuid4()}@example.com",
    )
    db_session.add(member)
    await db_session.commit()

    svc = AccessService(db_session)
    issued = await svc.issue_qr_token(tenant.id, member.id)
    await db_session.commit()

    result = await svc.validate_qr(tenant.id, issued.token, action="GYM_ENTRY")
    await db_session.commit()
    assert result.granted is False
    assert result.reason in (
        "NO_ACTIVE_MEMBERSHIP",
        "UNKNOWN_ACTION",
        "NO_WALLET",
        "NOT_ENTITLED",
    )


@pytest.mark.asyncio
async def test_issue_self_resolution_via_user_binding(db_session, tenant):
    """issue-self path: resolve member from user_id binding, never body member_id."""
    user = User(
        id=uuid4(),
        email=f"self-qr-{uuid4()}@example.com",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    members = MemberService(db_session)
    member = await members.create_member(
        tenant.id,
        member_number=f"SELF-{uuid4().hex[:6]}",
        first_name="Self",
        last_name="QR",
        user_id=user.id,
    )
    await db_session.commit()

    bound = await members.get_member_by_user_id(tenant.id, user.id)
    assert bound is not None
    assert bound.id == member.id

    # Unbound user → no member (API would 404)
    assert await members.get_member_by_user_id(tenant.id, uuid4()) is None

    svc = AccessService(db_session)
    issued = await svc.issue_qr_token(tenant.id, bound.id, ttl_seconds=60)
    await db_session.commit()
    assert issued.token
    assert issued.credential_id


@pytest.mark.asyncio
async def test_signing_key_tenant_scoped_kids(db_session, tenant):
    """Same kid string allowed only once per tenant; different tenants independent."""
    svc = AccessService(db_session)
    k1 = await svc.ensure_active_key(tenant.id)
    await db_session.commit()

    org = Organization(name="T2", domain=f"t2-{uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t2 = Tenant(
        id=uuid4(),
        name="T2",
        organization_id=org.id,
        location_code=f"T2-{uuid4().hex[:4]}",
    )
    db_session.add(t2)
    await db_session.commit()

    # Force same kid on t2
    k2 = SigningKey(
        tenant_id=t2.id,
        kid=k1.kid,
        status=KeyStatus.ACTIVE,
        algorithm="HMAC_SHA256",
        key_material="local:hmac:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    )
    db_session.add(k2)
    await db_session.commit()

    found = (
        (await db_session.execute(select(SigningKey).where(SigningKey.kid == k1.kid)))
        .scalars()
        .all()
    )
    assert len(found) == 2
