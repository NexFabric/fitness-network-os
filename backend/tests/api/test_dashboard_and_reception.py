"""Test suite for Dashboard KPIs and Front Desk Reception Workspace."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.access import Checkin
from app.models.entitlement import (
    EntitlementDefinition,
    EntitlementType,
    EntitlementWallet,
)
from app.models.finance import BillingAccount, Invoice, Payment
from app.models.location import Location
from app.models.member import Member, Note, Tag
from app.models.membership import Membership, Plan, PlanVersion
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession


def _token_pair() -> tuple[str, str]:
    import hashlib
    raw = f"tok_{uuid4().hex}"
    return raw, hashlib.sha256(raw.encode()).hexdigest()


async def _ensure_perms(db: AsyncSession, names: list[str]) -> list[Permission]:
    from sqlalchemy import select
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


async def _staff_user(db: AsyncSession, tenant_id, role_name="GYM_ADMIN") -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"staff-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    perms_needed = [
        "gym:read",
        "members:read",
        "members:write",
        "checkins:read",
        "checkins:write",
        "reports:read",
    ]
    perms = await _ensure_perms(db, perms_needed)

    role = Role(
        name=f"{role_name}-{uuid4().hex[:8]}",
        description="staff test role",
        permissions=perms,
    )
    db.add(role)
    await db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant_id))
    db.add(UserSession(user_id=user.id, token_hash=th, expires_at=datetime.now(UTC) + timedelta(days=1)))
    await db.flush()
    return user, raw


@pytest.fixture
async def api_client(pg_session_maker):
    async def override_get_db():
        async with pg_session_maker() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_kpis_aggregation(api_client, pg_engine):
    """GET /api/v1/dashboard/kpis returns accurate aggregated numbers."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Dash Org", domain=f"dash-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Dash T",
            organization_id=org.id,
            location_code=f"D-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        _user, token = await _staff_user(db, tenant.id)

        loc = Location(id=uuid4(), tenant_id=tenant.id, name="Main Gym")
        db.add(loc)

        # 1 Active Member, 1 Inactive Member
        m1 = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"M1-{uuid4().hex[:4]}",
            first_name="Active",
            last_name="Member",
            status="ACTIVE",
        )
        m2 = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number=f"M2-{uuid4().hex[:4]}",
            first_name="Lead",
            last_name="Person",
            status="LEAD",
        )
        db.add_all([m1, m2])
        await db.flush()

        # Plan and Plan Version
        plan = Plan(id=uuid4(), tenant_id=tenant.id, name="Standard Plan", is_active=True)
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
        )
        db.add(pv)
        await db.flush()

        # Expiring Membership
        db.add(
            Membership(
                id=uuid4(),
                tenant_id=tenant.id,
                member_id=m1.id,
                plan_version_id=pv.id,
                status="ACTIVE",
                start_date=datetime.now(UTC) - timedelta(days=30),
                end_date=datetime.now(UTC) + timedelta(days=10),
            )
        )

        # Check-in today
        db.add(
            Checkin(
                id=uuid4(),
                tenant_id=tenant.id,
                member_id=m1.id,
                location_id=loc.id,
                checkin_time=datetime.now(UTC),
            )
        )

        # Billing Account, Invoice, Payment
        ba = BillingAccount(
            id=uuid4(),
            tenant_id=tenant.id,
            member_id=m1.id,
            currency="TRY",
            status="ACTIVE",
        )
        db.add(ba)
        await db.flush()

        # Open past-due invoice
        db.add(
            Invoice(
                id=uuid4(),
                tenant_id=tenant.id,
                billing_account_id=ba.id,
                invoice_number="INV-PAST-1",
                status="OPEN",
                total_amount_minor=15000,
                paid_amount_minor=5000,
                discount_amount_minor=0,
                due_date=datetime.now(UTC) - timedelta(days=5),
                currency="TRY",
            )
        )

        # Succeeded payment this month
        db.add(
            Payment(
                id=uuid4(),
                tenant_id=tenant.id,
                billing_account_id=ba.id,
                amount_minor=5000,
                status="SUCCEEDED",
                currency="TRY",
                method="CREDIT_CARD",
            )
        )
        await db.commit()
        tenant_id = tenant.id

    r = await api_client.get(
        "/api/v1/dashboard/kpis",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["active_members_count"] == 1
    assert data["expiring_memberships_count"] == 1
    assert data["today_checkins_count"] == 1
    assert data["past_due_invoices_count"] == 1
    assert data["past_due_invoices_amount_minor"] == 10000
    assert data["month_collected_amount_minor"] == 5000
    assert data["total_outstanding_debt_minor"] == 10000


@pytest.mark.asyncio
async def test_reception_search_and_override_checkin(api_client, pg_engine):
    """Front desk reception search, detailed member card, and manual check-in override."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Rec Org", domain=f"rec-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Rec T",
            organization_id=org.id,
            location_code=f"R-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        staff_user, token = await _staff_user(db, tenant.id)

        loc = Location(id=uuid4(), tenant_id=tenant.id, name="Central Branch")
        db.add(loc)

        m = Member(
            id=uuid4(),
            tenant_id=tenant.id,
            member_number="MBR-9988",
            first_name="Kemal",
            last_name="Aydin",
            email="kemal@example.com",
            phone="+905551234567",
            status="ACTIVE",
        )
        db.add(m)
        await db.flush()

        db.add(Tag(tenant_id=tenant.id, member_id=m.id, name="VIP"))
        db.add(Note(tenant_id=tenant.id, member_id=m.id, content="Antrenör eşliğinde çalışıyor"))

        await db.commit()
        tenant_id = tenant.id
        member_id = m.id
        loc_id = loc.id

    # 1. Search members
    r_search = await api_client.get(
        "/api/v1/reception/search?q=Kemal",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
    )
    assert r_search.status_code == 200, r_search.text
    search_res = r_search.json()
    assert len(search_res) == 1
    assert search_res[0]["member_number"] == "MBR-9988"

    # 2. Get detailed member card
    r_detail = await api_client.get(
        f"/api/v1/reception/member/{member_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
    )
    assert r_detail.status_code == 200, r_detail.text
    detail = r_detail.json()
    assert detail["first_name"] == "Kemal"
    assert "VIP" in detail["tags"]
    assert "Antrenör eşliğinde çalışıyor" in detail["notes"]

    # 3. Manual override checkin
    r_override = await api_client.post(
        f"/api/v1/reception/checkin/{member_id}/override",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": str(tenant_id),
        },
        json={
            "location_id": str(loc_id),
            "reason": "Kartını evde unutmuş, kimlik kontrolüyle geçiş verildi.",
        },
    )
    assert r_override.status_code == 201, r_override.text
    override_res = r_override.json()
    assert override_res["member_id"] == str(member_id)
    assert override_res["location_id"] == str(loc_id)
    assert "başarıyla" in override_res["message"]
