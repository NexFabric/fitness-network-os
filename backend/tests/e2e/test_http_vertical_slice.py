"""Phase 18 P1-5 — HTTP/ASGI vertical slice (not service-layer only).

Covers a real ASGI request path:

  GET /health
  → POST /api/v1/auth/login (email/password → session token)
  → GET /api/v1/locations + GET /api/v1/members (Bearer + X-Tenant-ID)
  → POST /api/v1/access/qr/issue + POST /api/v1/access/qr/validate (GRANT)

Uses the same Postgres fixtures (pg_engine / pg_session_maker) and
AsyncClient(ASGITransport) pattern as ``tests/api/test_auth_login.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import get_password_hash
from app.db.session import get_db
from app.main import app
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
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User

# Staff surface for list + QR issue/validate (aligned with access endpoints).
STAFF_SLICE_PERMS = [
    "members:read",
    "locations:read",
    "access:issue",
    "access:validate",
]


@pytest.fixture
async def api_client(pg_session_maker):
    async def override_get_db():
        async with pg_session_maker() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


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


async def _seed_http_slice(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> tuple[Tenant, Member, Location]:
    """Org → tenant → staff user (password) → member + location + GYM_ENTRY wallet."""
    org = Organization(
        name=f"HTTP E2E Org {uuid4().hex[:6]}",
        domain=f"http-e2e-{uuid4().hex[:8]}.test",
    )
    db.add(org)
    await db.flush()

    tenant = Tenant(
        id=uuid4(),
        name="HTTP E2E Tenant",
        organization_id=org.id,
        location_code=f"H-{uuid4().hex[:6]}",
    )
    db.add(tenant)
    await db.flush()

    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    perms = await _ensure_perms(db, STAFF_SLICE_PERMS)
    role = Role(
        name=f"STAFF-HTTP-{uuid4().hex[:8]}",
        description="http e2e staff clone",
        permissions=perms,
    )
    db.add(role)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id))
    await db.flush()

    loc = Location(
        tenant_id=tenant.id,
        name="HTTP E2E Main",
        timezone="UTC",
    )
    db.add(loc)
    await db.flush()

    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"HTTP-{uuid4().hex[:6]}",
        first_name="Http",
        last_name="Slice",
        email=f"member-{uuid4().hex[:6]}@example.com",
        status="ACTIVE",
    )
    db.add(member)
    await db.flush()

    plan = Plan(
        id=uuid4(),
        tenant_id=tenant.id,
        name="HTTP E2E Plan",
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
    await db.commit()
    return tenant, member, loc


@pytest.mark.asyncio
async def test_http_vertical_slice_login_list_qr(
    api_client: AsyncClient,
    pg_engine,
):
    """ASGI path: health → login → locations/members → QR issue → validate GRANT."""
    email = f"http-e2e-{uuid4().hex[:8]}@example.com"
    password = "HttpSlicePass1!"

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        tenant, member, loc = await _seed_http_slice(db, email=email, password=password)
        tenant_id = tenant.id
        member_id = member.id
        location_id = loc.id

    # 1) Public health (no auth)
    health = await api_client.get("/health")
    assert health.status_code == 200, health.text
    assert health.json()["status"] in ("ok", "degraded")

    # 2) Login creates session token (real HTTP auth surface)
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    body = login.json()
    token = login.cookies.get("session_token")
    assert token and len(token) > 20
    assert body["tenant_id"] == str(tenant_id)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }

    # 3) Authenticated tenant-scoped lists
    locs = await api_client.get("/api/v1/locations", headers=headers)
    assert locs.status_code == 200, locs.text
    loc_ids = {row["id"] for row in locs.json()}
    assert str(location_id) in loc_ids

    members = await api_client.get("/api/v1/members", headers=headers)
    assert members.status_code == 200, members.text
    member_ids = {row["id"] for row in members.json()}
    assert str(member_id) in member_ids

    # 4) Staff QR issue (signing key created lazily) + validate GRANT
    issued = await api_client.post(
        "/api/v1/access/qr/issue",
        headers=headers,
        json={"member_id": str(member_id), "ttl_seconds": 60},
    )
    assert issued.status_code == 200, issued.text
    issued_body = issued.json()
    assert issued_body["token"].count(".") == 1
    assert issued_body["jti"]
    assert issued_body["kid"]
    assert issued_body["member_id"] == str(member_id)

    validated = await api_client.post(
        "/api/v1/access/qr/validate",
        headers=headers,
        json={
            "token": issued_body["token"],
            "location_id": str(location_id),
            "action": "GYM_ENTRY",
        },
    )
    assert validated.status_code == 200, validated.text
    vbody = validated.json()
    assert vbody["granted"] is True
    assert vbody["member_id"] == str(member_id)
    assert vbody["jti"] == issued_body["jti"]
    assert vbody["attempt_id"] is not None
    assert vbody["checkin_id"] is not None
