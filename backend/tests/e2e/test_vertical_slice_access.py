"""Phase 18 vertical slice — org → tenant → MEMBER user → member → QR access.

Real PostgreSQL (pg_engine / migrations), same fixture style as services/access
and phase15.5c session-token seeding. Service-layer path (not full ASGI HTTP)
covers the critical domain chain:

  Organization + Tenant
  → User (MEMBER perms) + UserSession token_hash
  → Member bound to user_id
  → active Membership + GYM_ENTRY entitlement wallet
  → issue-self resolution (MemberService.get_member_by_user_id)
  → AccessService.issue_qr_token + validate_qr (GRANT)
  → optional NotificationBridge.schedule_for_member_user (arch-safe helper)
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.event_types import MEMBERSHIP_ACTIVATED_V1, NOTIFICATION_REQUESTED_V1
from app.models.access import AccessAttempt, AccessStatus
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
from app.models.notification import DELIVERY_QUEUED, NotificationDelivery
from app.models.organization import Organization
from app.models.outbox import OutboxEvent
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession
from app.services.access import AccessService
from app.services.member import MemberService
from app.services.notification import NotificationService
from app.services.notification_bridge import NotificationBridge


# MEMBER self-service surface (aligned with phase15.5c / notifications RBAC tests).
MEMBER_SELF_PERMS = [
    "profile:read",
    "profile:write",
    "memberships:read:self",
    "checkins:read:self",
    "checkins:write:self",
    "entitlements:read:self",
    "entitlements:check:self",
    "access:issue:self",
]


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


def _token_pair() -> tuple[str, str]:
    """Raw bearer + sha256 hash stored on UserSession (phase15.5c pattern)."""
    raw = f"tok_{uuid4().hex}"
    return raw, hashlib.sha256(raw.encode()).hexdigest()


async def _ensure_perms(db: AsyncSession, names: list[str]) -> list[Permission]:
    out: list[Permission] = []
    for name in names:
        row = (
            await db.execute(select(Permission).where(Permission.name == name))
        ).scalar_one_or_none()
        if row is None:
            row = Permission(name=name, description=name)
            db.add(row)
            await db.flush()
        out.append(row)
    return out


async def _seed_org_tenant(db: AsyncSession) -> Tenant:
    org = Organization(
        name="E2E Slice Org",
        domain=f"e2e-slice-{uuid4().hex[:8]}.com",
    )
    db.add(org)
    await db.flush()
    tenant = Tenant(
        id=uuid4(),
        name="E2E Slice Tenant",
        organization_id=org.id,
        location_code=f"E2E-{uuid4().hex[:6]}",
    )
    db.add(tenant)
    await db.flush()
    return tenant


async def _user_with_member_role(
    db: AsyncSession,
    *,
    tenant_id,
    email_prefix: str = "e2e-member",
) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"{email_prefix}-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    perms = await _ensure_perms(db, MEMBER_SELF_PERMS)
    # Role.name is globally unique — clone name; authz matches permissions.
    role = Role(
        name=f"MEMBER-{uuid4().hex[:8]}",
        description="e2e clone of MEMBER",
        permissions=perms,
    )
    db.add(role)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant_id))
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=th,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    await db.flush()
    return user, raw


async def _seed_active_entry_entitlement(
    db: AsyncSession,
    tenant: Tenant,
    member: Member,
) -> Location:
    """Plan + ACTIVE membership + GYM_ENTRY wallet so validate_qr can GRANT."""
    loc = Location(tenant_id=tenant.id, name="E2E Main", timezone="UTC")
    db.add(loc)
    await db.flush()

    plan = Plan(
        id=uuid4(),
        tenant_id=tenant.id,
        name="E2E Access Plan",
        is_active=True,
    )
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
    await db.flush()
    return loc


@pytest.mark.asyncio
async def test_vertical_slice_org_member_qr_issue_validate(db_session: AsyncSession):
    """Full access vertical slice: bind → issue-self resolve → issue → validate GRANT."""
    tenant = await _seed_org_tenant(db_session)
    user, raw_token = await _user_with_member_role(db_session, tenant_id=tenant.id)
    assert raw_token.startswith("tok_")

    members = MemberService(db_session)
    member = await members.create_member(
        tenant.id,
        member_number=f"E2E-{uuid4().hex[:6]}",
        first_name="Slice",
        last_name="Member",
        email=f"slice-{uuid4().hex[:6]}@example.com",
        user_id=user.id,
    )
    loc = await _seed_active_entry_entitlement(db_session, tenant, member)
    await db_session.commit()

    # issue-self style resolution: never trust client member_id
    bound = await members.get_member_by_user_id(tenant.id, user.id)
    assert bound is not None
    assert bound.id == member.id
    assert bound.user_id == user.id
    assert await members.get_member_by_user_id(tenant.id, uuid4()) is None

    # Signing keys are created lazily on first issue (tenant-scoped ACTIVE key).
    access = AccessService(db_session)
    issued = await access.issue_qr_token(tenant.id, bound.id, ttl_seconds=60)
    await db_session.commit()

    assert issued.token.count(".") == 1
    assert issued.jti
    assert issued.kid
    assert issued.credential_id
    assert issued.exp > issued.iat

    result = await access.validate_qr(
        tenant.id,
        issued.token,
        location_id=loc.id,
        action="GYM_ENTRY",
    )
    await db_session.commit()

    assert result.granted is True
    assert result.reason is None or result.reason == "OK"
    assert result.member_id == member.id
    assert result.jti == issued.jti
    assert result.attempt_id is not None
    assert result.checkin_id is not None

    attempts = (
        await db_session.execute(
            select(AccessAttempt).where(AccessAttempt.tenant_id == tenant.id)
        )
    ).scalars().all()
    assert len(attempts) == 1
    assert attempts[0].status == AccessStatus.GRANTED
    assert attempts[0].member_id == member.id
    assert attempts[0].jti == issued.jti


@pytest.mark.asyncio
async def test_vertical_slice_staff_issue_validate_structured(
    db_session: AsyncSession,
):
    """Staff-style issue (explicit member_id) + structured ValidateQrResult."""
    tenant = await _seed_org_tenant(db_session)
    user, _raw = await _user_with_member_role(
        db_session, tenant_id=tenant.id, email_prefix="e2e-staff-path"
    )
    members = MemberService(db_session)
    member = await members.create_member(
        tenant.id,
        member_number=f"STF-{uuid4().hex[:6]}",
        first_name="Staff",
        last_name="Path",
        user_id=user.id,
    )
    loc = await _seed_active_entry_entitlement(db_session, tenant, member)
    await db_session.commit()

    access = AccessService(db_session)
    # Staff path: body.member_id is explicit (API enforces access:issue separately).
    issued = await access.issue_qr_token(tenant.id, member.id, ttl_seconds=120)
    await db_session.commit()

    denied_malformed = await access.validate_qr(tenant.id, "not-a-token")
    await db_session.commit()
    assert denied_malformed.granted is False
    assert denied_malformed.reason == "malformed_token"

    granted = await access.validate_qr(
        tenant.id,
        issued.token,
        location_id=loc.id,
        action="GYM_ENTRY",
    )
    await db_session.commit()
    assert granted.granted is True
    assert granted.member_id == member.id
    assert granted.attempt_id is not None


@pytest.mark.asyncio
async def test_vertical_slice_optional_notification_bridge(
    db_session: AsyncSession,
):
    """Optional: NotificationBridge after domain bind (does not touch MembershipService).

    Architecture rule: Membership must not import notification*; bridge is the
    allowed orchestrator-side path for domain → notification.requested.
    """
    tenant = await _seed_org_tenant(db_session)
    user, _raw = await _user_with_member_role(
        db_session, tenant_id=tenant.id, email_prefix="e2e-notif"
    )
    members = MemberService(db_session)
    member = await members.create_member(
        tenant.id,
        member_number=f"NTF-{uuid4().hex[:6]}",
        first_name="Ada",
        last_name="Notify",
        user_id=user.id,
    )
    await db_session.commit()

    bound = await members.get_member_by_user_id(tenant.id, user.id)
    assert bound is not None and bound.id == member.id

    nsvc = NotificationService(db_session)
    await nsvc.create_template(
        tenant.id,
        code="membership_activated",
        name="Membership activated",
        channel="EMAIL",
        subject_template="Welcome $first_name",
        body_template="Hi $first_name, access ready at $gym_name.",
    )
    await db_session.commit()

    bridge = NotificationBridge(db_session)
    membership_id = uuid4()
    domain_event_id = str(uuid4())
    scheduled = await bridge.schedule_for_member_user(
        tenant.id,
        user.id,
        template_code="membership_activated",
        channel="EMAIL",
        context={"first_name": "Ada", "gym_name": "GymClub"},
        dedupe_key=f"membership.activated:{membership_id}",
        correlation_id=f"corr-{membership_id}",
        source_event_type=MEMBERSHIP_ACTIVATED_V1,
        source_event_id=domain_event_id,
        enqueue_outbox=True,
    )
    await db_session.commit()

    assert scheduled.created is True
    d = scheduled.delivery
    assert d.recipient_user_id == user.id
    assert d.status == DELIVERY_QUEUED
    assert d.subject == "Welcome Ada"
    assert "GymClub" in (d.body or "")
    assert d.source_event_type == MEMBERSHIP_ACTIVATED_V1
    assert scheduled.outbox_event_id is not None

    outbox_row = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.id == scheduled.outbox_event_id)
        )
    ).scalars().first()
    assert outbox_row is not None
    assert outbox_row.event_type == NOTIFICATION_REQUESTED_V1
    assert outbox_row.tenant_id == tenant.id

    deliveries = (
        await db_session.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.tenant_id == tenant.id
            )
        )
    ).scalars().all()
    assert len(deliveries) == 1
