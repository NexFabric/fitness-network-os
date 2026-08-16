"""Complete Federation Admin API test suite — lifecycle, passport, compliance, alerts, and analytics."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import app
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession


def _token_pair() -> tuple[str, str]:
    raw = f"tok_{uuid4().hex}"
    return raw, hashlib.sha256(raw.encode()).hexdigest()


async def _ensure_perm(db: AsyncSession, name: str) -> Permission:
    row = (
        await db.execute(select(Permission).where(Permission.name == name))
    ).scalar_one_or_none()
    if row is None:
        row = Permission(name=name, description=name)
        db.add(row)
        await db.flush()
    return row


async def _principal(
    db: AsyncSession,
    *,
    role_name: str,
    tenant_id=None,
    organization_id=None,
    perms: list[str] | None = None,
) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"{role_name.lower()}-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role = (
        await db.execute(select(Role).where(Role.name == role_name))
    ).scalar_one_or_none()
    if role is None:
        role = Role(
            name=role_name,
            description=role_name,
            permissions=[await _ensure_perm(db, p) for p in (perms or [])],
        )
        db.add(role)
        await db.flush()
    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
            organization_id=organization_id,
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


@pytest.mark.asyncio
async def test_tenant_lifecycle_flow(api_client, pg_session_maker):
    async with pg_session_maker() as db:
        # Setup Organization
        org = Organization(
            name="Lifecycle Federation", domain=f"lf-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()

        _, token = await _principal(
            db,
            role_name="FEDERATION_ADMIN",
            organization_id=org.id,
        )
        await db.commit()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Tenant
    loc_code = f"LOC-{uuid4().hex[:4].upper()}"
    res = await api_client.post(
        "/api/v1/admin/tenants",
        headers=headers,
        json={
            "organization_id": str(org.id),
            "name": "Yeni Test Kulübü",
            "location_code": loc_code,
            "initial_branch_name": "Ana Şube",
            "initial_branch_address": "Kadıköy, İstanbul",
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    tenant_id = data["id"]
    assert data["name"] == "Yeni Test Kulübü"
    assert data["status"] == "ACTIVE"

    # 2. Suspend Tenant
    res_suspend = await api_client.post(
        f"/api/v1/admin/tenants/{tenant_id}/suspend",
        headers=headers,
        json={"reason": "Denetim eksikliği ve aidat gecikmesi"},
    )
    assert res_suspend.status_code == 200
    assert res_suspend.json()["status"] == "SUSPENDED"
    assert (
        res_suspend.json()["suspension_reason"]
        == "Denetim eksikliği ve aidat gecikmesi"
    )

    # 3. Reactivate Tenant
    res_reactivate = await api_client.post(
        f"/api/v1/admin/tenants/{tenant_id}/reactivate",
        headers=headers,
    )
    assert res_reactivate.status_code == 200
    assert res_reactivate.json()["status"] == "ACTIVE"
    assert res_reactivate.json()["suspension_reason"] is None


@pytest.mark.asyncio
async def test_federation_passport_flow(api_client, pg_session_maker):
    async with pg_session_maker() as db:
        org = Organization(
            name="Passport Federation", domain=f"pf-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()

        tenant = Tenant(
            organization_id=org.id,
            name="Passport Club",
            location_code=f"PC-{uuid4().hex[:4].upper()}",
        )
        db.add(tenant)
        await db.flush()

        _, token = await _principal(
            db,
            role_name="FEDERATION_ADMIN",
            organization_id=org.id,
        )
        await db.commit()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update passport config
    res = await api_client.put(
        f"/api/v1/admin/tenants/{tenant.id}/passport",
        headers=headers,
        json={
            "is_active": True,
            "allowed_home_gym_tiers": "VIP,PLATINUM",
            "rules": {"max_monthly_roaming_visits": 8, "guest_fee_minor": 5000},
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["is_active"] is True
    assert data["allowed_home_gym_tiers"] == "VIP,PLATINUM"
    assert data["rules"]["max_monthly_roaming_visits"] == 8

    # 2. Get passport config
    res_get = await api_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/passport",
        headers=headers,
    )
    assert res_get.status_code == 200
    assert res_get.json()["is_active"] is True

    # 3. List configs
    res_list = await api_client.get("/api/v1/admin/passport/configs", headers=headers)
    assert res_list.status_code == 200
    assert any(c["tenant_id"] == str(tenant.id) for c in res_list.json())


@pytest.mark.asyncio
async def test_compliance_and_alerts_flow(api_client, pg_session_maker):
    async with pg_session_maker() as db:
        org = Organization(name="Audit Federation", domain=f"af-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()

        tenant = Tenant(
            organization_id=org.id,
            name="Audit Club",
            location_code=f"AC-{uuid4().hex[:4].upper()}",
        )
        db.add(tenant)
        await db.flush()

        _, token = await _principal(
            db,
            role_name="FEDERATION_ADMIN",
            organization_id=org.id,
        )
        await db.commit()

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Compliance Record
    res_comp = await api_client.post(
        f"/api/v1/admin/tenants/{tenant.id}/compliance",
        headers=headers,
        json={
            "certification_name": "TSE-ISO 9001 Hizmet Standardı",
            "status": "PASSED",
            "auditor_notes": "Tüm hijyen ve acil yardım kriterleri eksiksiz karşılandı.",
        },
    )
    assert res_comp.status_code == 201, res_comp.text
    comp_data = res_comp.json()
    assert comp_data["certification_name"] == "TSE-ISO 9001 Hizmet Standardı"
    assert comp_data["status"] == "PASSED"

    # 2. List compliance
    res_list_comp = await api_client.get("/api/v1/admin/compliance", headers=headers)
    assert res_list_comp.status_code == 200
    assert len(res_list_comp.json()) >= 1

    # 3. Broadcast Alert
    res_alert = await api_client.post(
        "/api/v1/admin/alerts",
        headers=headers,
        json={
            "organization_id": str(org.id),
            "title": "Ağ Geneli Güvenlik Güncellemesi",
            "message": "Turnike tarayıcı sistemleri saat 02:00'de güncellenecektir.",
            "severity": "WARNING",
        },
    )
    assert res_alert.status_code == 201, res_alert.text
    alert_id = res_alert.json()["id"]

    # 4. List Alerts
    res_list_alerts = await api_client.get("/api/v1/admin/alerts", headers=headers)
    assert res_list_alerts.status_code == 200
    assert any(a["id"] == alert_id for a in res_list_alerts.json())

    # 5. Delete Alert
    res_del = await api_client.delete(
        f"/api/v1/admin/alerts/{alert_id}", headers=headers
    )
    assert res_del.status_code == 204

    # 6. Analytics Overview
    res_analytics = await api_client.get(
        "/api/v1/admin/analytics/overview", headers=headers
    )
    assert res_analytics.status_code == 200
    assert "total_checkins" in res_analytics.json()
    assert "total_revenue_minor" in res_analytics.json()
