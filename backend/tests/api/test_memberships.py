import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.member import Member
from app.models.membership import Membership, Plan, PlanVersion
from app.models.rbac import Role, UserRole, Permission
from app.models.tenant import Tenant
from app.models.organization import Organization
from app.models.user import User, UserSession
from sqlalchemy import text


from app.db.session import get_db

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


@pytest.fixture
async def setup_data(pg_engine):
    tenant_a = uuid4()
    tenant_b = uuid4()
    token_a = "token_a_123"
    token_hash_a = hashlib.sha256(token_a.encode()).hexdigest()

    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    async_session = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Create organization and tenants
        org = Organization(name="Test Org", domain="test.com")
        db.add(org)
        await db.flush()

        tenant_a_obj = Tenant(id=tenant_a, name="Tenant A", location_code="TA", organization_id=org.id)
        tenant_b_obj = Tenant(id=tenant_b, name="Tenant B", location_code="TB", organization_id=org.id)
        db.add(tenant_a_obj)
        db.add(tenant_b_obj)
        await db.flush()

        # Create user A in tenant A
        user_a = User(
            email="usera@example.com",
            hashed_password="pw",
            is_active=True
        )
        db.add(user_a)
        await db.flush()

        perm = Permission(name="members:write")
        db.add(perm)
        await db.flush()

        role = Role(name="admin", permissions=[perm])
        db.add(role)
        await db.flush()

        role_a = UserRole(user_id=user_a.id, tenant_id=tenant_a, role_id=role.id)
        db.add(role_a)
        
        session_a = UserSession(
            user_id=user_a.id,
            token_hash=token_hash_a,
            expires_at=datetime.now(UTC) + timedelta(days=1)
        )
        db.add(session_a)
        await db.flush()

        # Create Member and Membership in Tenant B
        member_b = Member(
            tenant_id=tenant_b,
            member_number="M-B",
            first_name="B",
            last_name="B",
            status="ACTIVE"
        )
        db.add(member_b)
        await db.flush()
        
        plan_b = Plan(tenant_id=tenant_b, name="Plan B", description="B")
        db.add(plan_b)
        await db.flush()

        pv_b = PlanVersion(
            tenant_id=tenant_b,
            plan_id=plan_b.id,
            version=1,
            price_amount_minor=1000,
            billing_cycle_months=1
        )
        db.add(pv_b)
        await db.flush()
        
        membership_b = Membership(
            tenant_id=tenant_b,
            member_id=member_b.id,
            plan_version_id=pv_b.id,
            status="ACTIVE",
            start_date=datetime.now(UTC)
        )
        db.add(membership_b)
        
        # Membership in Tenant A to test successful freeze
        member_a = Member(
            tenant_id=tenant_a,
            member_number="M-A",
            first_name="A",
            last_name="A",
            status="ACTIVE"
        )
        db.add(member_a)
        await db.flush()
        
        plan_a = Plan(tenant_id=tenant_a, name="Plan A", description="A")
        db.add(plan_a)
        await db.flush()

        pv_a = PlanVersion(
            tenant_id=tenant_a,
            plan_id=plan_a.id,
            version=1,
            price_amount_minor=1000,
            billing_cycle_months=1
        )
        db.add(pv_a)
        await db.flush()
        
        membership_a = Membership(
            tenant_id=tenant_a,
            member_id=member_a.id,
            plan_version_id=pv_a.id,
            status="ACTIVE",
            start_date=datetime.now(UTC)
        )
        db.add(membership_a)

        await db.commit()

        return {
            "tenant_a": tenant_a,
            "tenant_b": tenant_b,
            "token_a": token_a,
            "membership_a_id": membership_a.id,
            "membership_b_id": membership_b.id
        }


@pytest.mark.asyncio
async def test_tenant_a_cannot_freeze_tenant_b_membership(api_client, setup_data):
    # Try to freeze Tenant B's membership using Tenant A's token and X-Tenant-ID
    headers = {
        "Authorization": f"Bearer {setup_data['token_a']}",
        "X-Tenant-ID": str(setup_data['tenant_a'])
    }
    
    start = datetime.now(UTC)
    end = start + timedelta(days=30)
    
    response = await api_client.post(
        f"/api/v1/memberships/{setup_data['membership_b_id']}/freeze",
        headers=headers,
        json={
            "start_date": start.isoformat(),
            "expected_end_date": end.isoformat(),
            "reason": "Test"
        }
    )
    
    # Membership B is in Tenant B. But we are querying it under Tenant A's context.
    # The get_membership service method should return None because RLS prevents Tenant A
    # from seeing Tenant B's rows.
    # The service raises ValueError("Membership not found") -> 400
    assert response.status_code == 400
    assert "Membership not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_tenant_a_cannot_use_tenant_b_header(api_client, setup_data):
    # User A tries to set X-Tenant-ID to Tenant B, which they don't have a role for
    headers = {
        "Authorization": f"Bearer {setup_data['token_a']}",
        "X-Tenant-ID": str(setup_data['tenant_b'])
    }
    
    start = datetime.now(UTC)
    end = start + timedelta(days=30)
    
    response = await api_client.post(
        f"/api/v1/memberships/{setup_data['membership_b_id']}/freeze",
        headers=headers,
        json={
            "start_date": start.isoformat(),
            "expected_end_date": end.isoformat(),
            "reason": "Test"
        }
    )
    
    # 403 Forbidden because User A doesn't have a role in Tenant B
    assert response.status_code == 403
    assert "User does not have access to this tenant" in response.json()["detail"]


@pytest.mark.asyncio
async def test_successful_freeze(api_client, setup_data):
    headers = {
        "Authorization": f"Bearer {setup_data['token_a']}",
        "X-Tenant-ID": str(setup_data['tenant_a'])
    }
    
    start = datetime.now(UTC)
    end = start + timedelta(days=30)
    
    response = await api_client.post(
        f"/api/v1/memberships/{setup_data['membership_a_id']}/freeze",
        headers=headers,
        json={
            "start_date": start.isoformat(),
            "expected_end_date": end.isoformat(),
            "reason": "Going on vacation"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["reason"] == "Going on vacation"
    assert data["tenant_id"] == str(setup_data['tenant_a'])
    assert data["membership_id"] == str(setup_data['membership_a_id'])
