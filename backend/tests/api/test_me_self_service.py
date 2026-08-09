"""Phase 17A — /me self-service expansion (bound member only; no client member_id)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.access import Checkin
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
from app.models.user import User, UserSession


def _token_pair() -> tuple[str, str]:
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


async def _user_with_role(
    db: AsyncSession,
    *,
    tenant_id,
    role_name: str,
    perm_names: list[str],
    email_prefix: str,
) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"{email_prefix}-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    perms = await _ensure_perms(db, perm_names)
    # Role.name is globally unique — use unique names; authz matches permissions, not role id.
    role = Role(
        name=f"{role_name}-{uuid4().hex[:8]}",
        description=f"test clone of {role_name}",
        permissions=perms,
    )
    db.add(role)
    await db.flush()
    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
        )
    )
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=th,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
    )
    await db.flush()
    return user, raw


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

STAFF_MEMBER_READ = [
    "members:read",
    "memberships:read",
    "entitlements:read",
    "entitlements:check",
    "checkins:read",
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


async def _seed_bound_member_with_membership(
    db: AsyncSession,
) -> tuple[Tenant, User, str, Member, Membership]:
    org = Organization(name="Me Org", domain=f"me-{uuid4().hex[:6]}.com")
    db.add(org)
    await db.flush()
    tenant = Tenant(
        id=uuid4(),
        name="Me T",
        organization_id=org.id,
        location_code=f"M-{uuid4().hex[:6]}",
    )
    db.add(tenant)
    await db.flush()

    user, token = await _user_with_role(
        db,
        tenant_id=tenant.id,
        role_name="MEMBER",
        perm_names=MEMBER_SELF_PERMS,
        email_prefix="me-bound",
    )
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"M-{uuid4().hex[:6]}",
        first_name="Self",
        last_name="Bound",
        email="self@example.com",
        phone="+10000000001",
        status="ACTIVE",
        user_id=user.id,
    )
    db.add(member)
    await db.flush()

    plan = Plan(tenant_id=tenant.id, name="Plan Me", description="me")
    db.add(plan)
    await db.flush()
    pv = PlanVersion(
        tenant_id=tenant.id,
        plan_id=plan.id,
        version=1,
        price_amount_minor=5000,
        billing_cycle_months=1,
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
        start_date=datetime.now(UTC) - timedelta(days=10),
        end_date=datetime.now(UTC) + timedelta(days=20),
    )
    db.add(membership)
    await db.flush()
    return tenant, user, token, member, membership


@pytest.mark.asyncio
async def test_me_profile_member_memberships_bound_allow(api_client, pg_engine):
    """MEMBER with user↔member binding ALLOW on /me/profile, /member, /memberships."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        tenant, user, token, member, membership = (
            await _seed_bound_member_with_membership(db)
        )
        await db.commit()
        tenant_id = tenant.id
        member_id = member.id
        membership_id = membership.id
        user_id = user.id

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }

    r_profile = await api_client.get("/api/v1/me/profile", headers=headers)
    assert r_profile.status_code == 200, r_profile.text
    pbody = r_profile.json()
    assert pbody["user_id"] == str(user_id)
    assert pbody["tenant_id"] == str(tenant_id)
    assert pbody["member"]["id"] == str(member_id)
    assert pbody["member"]["first_name"] == "Self"

    r_member = await api_client.get("/api/v1/me/member", headers=headers)
    assert r_member.status_code == 200, r_member.text
    body = r_member.json()
    assert body["id"] == str(member_id)
    assert body["tenant_id"] == str(tenant_id)
    assert body["user_id"] == str(user_id)
    assert body["first_name"] == "Self"
    assert body["last_name"] == "Bound"
    assert body["status"] == "ACTIVE"
    assert body["member_number"].startswith("M-")

    r_ms = await api_client.get("/api/v1/me/memberships", headers=headers)
    assert r_ms.status_code == 200, r_ms.text
    items = r_ms.json()
    assert len(items) == 1
    assert items[0]["id"] == str(membership_id)
    assert items[0]["member_id"] == str(member_id)
    assert items[0]["tenant_id"] == str(tenant_id)
    assert items[0]["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_me_entitlements_list_bound(api_client, pg_engine):
    """GET /me/entitlements returns wallet snapshot for bound member only."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        tenant, _user, token, member, membership = (
            await _seed_bound_member_with_membership(db)
        )
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
        # Other member wallet must not appear
        other = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"O-{uuid4().hex[:6]}",
            first_name="Other",
            last_name="Mem",
            status="ACTIVE",
            user_id=None,
        )
        db.add(other)
        await db.flush()
        plan2 = Plan(tenant_id=tenant.id, name="Other Plan")
        db.add(plan2)
        await db.flush()
        pv2 = PlanVersion(
            tenant_id=tenant.id,
            plan_id=plan2.id,
            version=1,
            price_amount_minor=1000,
            billing_cycle_months=1,
            is_published=True,
            published_at=datetime.now(UTC),
        )
        db.add(pv2)
        await db.flush()
        mem_other = Membership(
            id=uuid4(),
            tenant_id=tenant.id,
            member_id=other.id,
            plan_version_id=pv2.id,
            status="ACTIVE",
            start_date=datetime.now(UTC),
            end_date=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(mem_other)
        await db.flush()
        me_other = MembershipEntitlement(
            id=uuid4(),
            tenant_id=tenant.id,
            membership_id=mem_other.id,
            entitlement_id=ent.id,
            granted_quantity=50,
            unlimited=False,
            status=MembershipEntitlementStatus.ACTIVE.value,
        )
        db.add(me_other)
        await db.flush()
        db.add(
            EntitlementWallet(
                id=uuid4(),
                tenant_id=tenant.id,
                member_id=other.id,
                membership_id=mem_other.id,
                membership_entitlement_id=me_other.id,
                entitlement_id=ent.id,
                allocated=50,
                remaining=50,
                reserved=0,
                consumed=0,
            )
        )
        await db.commit()
        tenant_id = tenant.id
        member_id = member.id
        wallet_id = wallet.id

    r = await api_client.get(
        "/api/v1/me/entitlements",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["member_id"] == str(member_id)
    assert len(body["wallets"]) == 1
    assert body["wallets"][0]["wallet_id"] == str(wallet_id)
    assert body["wallets"][0]["entitlement_code"] == "GYM_ENTRY"
    assert body["wallets"][0]["remaining"] == 1


@pytest.mark.asyncio
async def test_me_checkins_list_bound(api_client, pg_engine):
    """GET /me/checkins lists only bound member checkins."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        tenant, _user, token, member, _membership = (
            await _seed_bound_member_with_membership(db)
        )
        loc = Location(tenant_id=tenant.id, name="Main", timezone="UTC")
        db.add(loc)
        await db.flush()
        own_ci = Checkin(
            id=uuid4(),
            tenant_id=tenant.id,
            member_id=member.id,
            location_id=loc.id,
            checkin_time=datetime.now(UTC),
        )
        db.add(own_ci)
        other = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"X-{uuid4().hex[:6]}",
            first_name="Other",
            last_name="Check",
            status="ACTIVE",
        )
        db.add(other)
        await db.flush()
        db.add(
            Checkin(
                id=uuid4(),
                tenant_id=tenant.id,
                member_id=other.id,
                location_id=loc.id,
                checkin_time=datetime.now(UTC),
            )
        )
        await db.commit()
        tenant_id = tenant.id
        member_id = member.id
        checkin_id = own_ci.id

    r = await api_client.get(
        "/api/v1/me/checkins",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
    )
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) == 1
    assert items[0]["id"] == str(checkin_id)
    assert items[0]["member_id"] == str(member_id)


@pytest.mark.asyncio
async def test_me_routes_wrong_tenant_deny(api_client, pg_engine):
    """Role in tenant A must not pass require_self against tenant B header."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="XTenant Org", domain=f"xt-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant_a = Tenant(
            id=uuid4(),
            name="T-A",
            organization_id=org.id,
            location_code=f"A-{uuid4().hex[:6]}",
        )
        tenant_b = Tenant(
            id=uuid4(),
            name="T-B",
            organization_id=org.id,
            location_code=f"B-{uuid4().hex[:6]}",
        )
        db.add_all([tenant_a, tenant_b])
        await db.flush()

        user, token = await _user_with_role(
            db,
            tenant_id=tenant_a.id,
            role_name="MEMBER",
            perm_names=MEMBER_SELF_PERMS,
            email_prefix="me-xta",
        )
        member_a = Member(
            id=uuid4(),
            tenant_id=tenant_a.id,
            member_number=f"A-{uuid4().hex[:6]}",
            first_name="A",
            last_name="Mem",
            status="ACTIVE",
            user_id=user.id,
        )
        member_b = Member(
            id=uuid4(),
            tenant_id=tenant_b.id,
            member_number=f"B-{uuid4().hex[:6]}",
            first_name="B",
            last_name="Mem",
            status="ACTIVE",
            user_id=user.id,
        )
        db.add_all([member_a, member_b])
        await db.commit()
        tenant_b_id = tenant_b.id

    headers_wrong = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_b_id),
    }

    for path in (
        "/api/v1/me/profile",
        "/api/v1/me/member",
        "/api/v1/me/memberships",
        "/api/v1/me/entitlements",
        "/api/v1/me/checkins",
    ):
        r = await api_client.get(path, headers=headers_wrong)
        assert r.status_code == 403, (path, r.status_code, r.text)


@pytest.mark.asyncio
async def test_me_routes_unbound_404(api_client, pg_engine):
    """MEMBER with self perms but no members.user_id binding → 404 member_not_bound."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Unbound Me", domain=f"ubm-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Unbound T",
            organization_id=org.id,
            location_code=f"U-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        _user, token = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="MEMBER",
            perm_names=MEMBER_SELF_PERMS,
            email_prefix="me-unbound",
        )
        db.add(
            Member(
                id=uuid4(),
                tenant_id=tenant.id,
                member_number=f"X-{uuid4().hex[:6]}",
                first_name="Other",
                last_name="Person",
                status="ACTIVE",
                user_id=None,
            )
        )
        await db.commit()
        tenant_id = tenant.id

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }

    for path in (
        "/api/v1/me/profile",
        "/api/v1/me/member",
        "/api/v1/me/memberships",
        "/api/v1/me/entitlements",
        "/api/v1/me/checkins",
    ):
        r = await api_client.get(path, headers=headers)
        assert r.status_code == 404, (path, r.status_code, r.text)
        assert r.json()["detail"] == "member_not_bound"


@pytest.mark.asyncio
async def test_me_no_client_member_id_path_and_staff_path_unchanged(
    api_client, pg_engine
):
    """BOLA: MEMBER cannot use staff member path; /me has no foreign member_id param."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="BOLA Me", domain=f"bola-me-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="BOLA T",
            organization_id=org.id,
            location_code=f"B-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        user_a, token_a = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="MEMBER",
            perm_names=MEMBER_SELF_PERMS,
            email_prefix="bola-a",
        )
        user_b, _token_b = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="MEMBER",
            perm_names=MEMBER_SELF_PERMS,
            email_prefix="bola-b",
        )
        member_a = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"A-{uuid4().hex[:6]}",
            first_name="A",
            last_name="Mem",
            status="ACTIVE",
            user_id=user_a.id,
        )
        member_b = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"B-{uuid4().hex[:6]}",
            first_name="B",
            last_name="Mem",
            status="ACTIVE",
            user_id=user_b.id,
        )
        db.add_all([member_a, member_b])
        await db.commit()
        tenant_id = tenant.id
        member_b_id = member_b.id

    headers_a = {
        "Authorization": f"Bearer {token_a}",
        "X-Tenant-ID": str(tenant_id),
    }

    # Staff path: MEMBER lacks members:read → 403
    r_staff = await api_client.get(
        f"/api/v1/members/{member_b_id}", headers=headers_a
    )
    assert r_staff.status_code == 403

    # Self path returns A only
    r_self = await api_client.get("/api/v1/me/member", headers=headers_a)
    assert r_self.status_code == 200
    assert r_self.json()["first_name"] == "A"

    # Query param pollution ignored — no member_id on /me routes
    r_pollute = await api_client.get(
        f"/api/v1/me/memberships?member_id={member_b_id}",
        headers=headers_a,
    )
    assert r_pollute.status_code == 200
    assert r_pollute.json() == []  # A has no memberships in this seed


@pytest.mark.asyncio
async def test_me_entitlements_check_still_works(api_client, pg_engine):
    """Regression: POST /me/entitlements/check remains functional."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        tenant, _user, token, member, _ = await _seed_bound_member_with_membership(db)
        await db.commit()
        tenant_id = tenant.id
        member_id = member.id

    r = await api_client.post(
        "/api/v1/me/entitlements/check",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
        json={"action": "GYM_ENTRY", "quantity": 1},
    )
    assert r.status_code == 200
    assert r.json()["member_id"] == str(member_id)
    assert "granted" in r.json()


@pytest.mark.asyncio
async def test_staff_members_list_unchanged(api_client, pg_engine):
    """Staff path with members:read still works (no regression)."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Staff Org", domain=f"st-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Staff T",
            organization_id=org.id,
            location_code=f"S-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        _user, token = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="GYM_ADMIN",
            perm_names=STAFF_MEMBER_READ,
            email_prefix="staff",
        )
        db.add(
            Member(
                id=uuid4(),
                tenant_id=tenant.id,
                member_number=f"S-{uuid4().hex[:6]}",
                first_name="Staff",
                last_name="View",
                status="ACTIVE",
            )
        )
        await db.commit()
        tenant_id = tenant.id

    r = await api_client.get(
        "/api/v1/members",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
    )
    assert r.status_code == 200
    assert len(r.json()) >= 1
