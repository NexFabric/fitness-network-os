"""Phase 16 — notifications/reports API RBAC + schedule body contract."""

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
    # Role.name is globally unique — use unique names; authz matches permissions.
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
async def test_member_forbidden_create_template_and_definition(api_client, pg_engine):
    """MEMBER token must not create notification templates or report definitions."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(
            name="P16 RBAC Org", domain=f"p16-rbac-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="P16 RBAC T",
            organization_id=org.id,
            location_code=f"P16-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        member_self_perms = [
            "profile:read",
            "profile:write",
            "memberships:read:self",
            "checkins:read:self",
            "checkins:write:self",
            "entitlements:read:self",
            "entitlements:check:self",
            "access:issue:self",
        ]
        _user, token = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="MEMBER",
            perm_names=member_self_perms,
            email_prefix="p16-mem",
        )
        await db.commit()
        tenant_id = tenant.id

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }

    tmpl = await api_client.post(
        "/api/v1/notifications/templates",
        headers=headers,
        json={
            "code": "welcome",
            "name": "Welcome",
            "channel": "EMAIL",
            "body_template": "Hi $name",
        },
    )
    assert tmpl.status_code == 403

    defn = await api_client.post(
        "/api/v1/reports/definitions",
        headers=headers,
        json={
            "code": "daily",
            "name": "Daily report",
            "report_type": "GENERIC",
        },
    )
    assert defn.status_code == 403


@pytest.mark.asyncio
async def test_staff_with_write_perms_create_template_and_definition(
    api_client, pg_engine
):
    """Staff with notifications:write / reports:write → 201 on create."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(
            name="P16 Staff Org", domain=f"p16-staff-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="P16 Staff T",
            organization_id=org.id,
            location_code=f"PS-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        _user, token = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="GYM_ADMIN",
            perm_names=["notifications:write", "reports:write"],
            email_prefix="p16-staff",
        )
        await db.commit()
        tenant_id = tenant.id

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }

    tmpl = await api_client.post(
        "/api/v1/notifications/templates",
        headers=headers,
        json={
            "code": f"welcome-{uuid4().hex[:6]}",
            "name": "Welcome",
            "channel": "EMAIL",
            "body_template": "Hi $name",
            "subject_template": "Welcome",
        },
    )
    assert tmpl.status_code == 201, tmpl.text
    body = tmpl.json()
    assert body["channel"] == "EMAIL"
    assert body["tenant_id"] == str(tenant_id)

    defn = await api_client.post(
        "/api/v1/reports/definitions",
        headers=headers,
        json={
            "code": f"daily-{uuid4().hex[:6]}",
            "name": "Daily report",
            "report_type": "GENERIC",
            "config": {"metric": "checkins"},
        },
    )
    assert defn.status_code == 201, defn.text
    dbody = defn.json()
    assert dbody["report_type"] == "GENERIC"
    assert dbody["tenant_id"] == str(tenant_id)


@pytest.mark.asyncio
async def test_delivery_schedule_body_does_not_require_enqueue_outbox(
    api_client, pg_engine
):
    """POST /notifications/deliveries must accept body without enqueue_outbox."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(
            name="P16 Sched Org", domain=f"p16-sched-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="P16 Sched T",
            organization_id=org.id,
            location_code=f"SC-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        _user, token = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="FRONT_DESK",
            perm_names=["notifications:write", "notifications:send"],
            email_prefix="p16-fd",
        )
        await db.commit()
        tenant_id = tenant.id

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }

    code = f"sched-{uuid4().hex[:6]}"
    tmpl = await api_client.post(
        "/api/v1/notifications/templates",
        headers=headers,
        json={
            "code": code,
            "name": "Schedule tpl",
            "channel": "EMAIL",
            "body_template": "ping",
        },
    )
    assert tmpl.status_code == 201, tmpl.text

    # Intentionally omit enqueue_outbox — must not be required by the contract
    payload = {
        "channel": "EMAIL",
        "recipient_address": "member@example.com",
        "template_code": code,
    }
    assert "enqueue_outbox" not in payload

    sched = await api_client.post(
        "/api/v1/notifications/deliveries",
        headers=headers,
        json=payload,
    )
    assert sched.status_code == 201, sched.text
    data = sched.json()
    assert data["status"] in ("QUEUED", "PENDING", "SENT")
    assert data["channel"] == "EMAIL"
    assert data["recipient_address"] == "member@example.com"


@pytest.mark.asyncio
async def test_delivery_and_run_dedupe_returns_200(api_client, pg_engine):
    """First create → 201; same dedupe_key → 200 with created=false (IR-001 / 15.6)."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(
            name="P16 Dedupe Org", domain=f"p16-dedupe-{uuid4().hex[:6]}.com"
        )
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="P16 Dedupe T",
            organization_id=org.id,
            location_code=f"DD-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        _user, token = await _user_with_role(
            db,
            tenant_id=tenant.id,
            role_name="FRONT_DESK",
            perm_names=[
                "notifications:write",
                "notifications:send",
                "reports:write",
                "reports:run",
            ],
            email_prefix="p16-dd",
        )
        await db.commit()
        tenant_id = tenant.id

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }

    tmpl_code = f"dd-tpl-{uuid4().hex[:6]}"
    tmpl = await api_client.post(
        "/api/v1/notifications/templates",
        headers=headers,
        json={
            "code": tmpl_code,
            "name": "Dedupe tpl",
            "channel": "EMAIL",
            "body_template": "hello",
        },
    )
    assert tmpl.status_code == 201, tmpl.text

    dedupe = f"notify:{uuid4().hex}"
    first = await api_client.post(
        "/api/v1/notifications/deliveries",
        headers=headers,
        json={
            "channel": "EMAIL",
            "recipient_address": "member@example.com",
            "template_code": tmpl_code,
            "dedupe_key": dedupe,
        },
    )
    assert first.status_code == 201, first.text
    assert first.json()["created"] is True
    first_id = first.json()["id"]

    second = await api_client.post(
        "/api/v1/notifications/deliveries",
        headers=headers,
        json={
            "channel": "EMAIL",
            "recipient_address": "member@example.com",
            "template_code": tmpl_code,
            "dedupe_key": dedupe,
        },
    )
    assert second.status_code == 200, second.text
    assert second.json()["created"] is False
    assert second.json()["id"] == first_id

    defn_code = f"dd-rpt-{uuid4().hex[:6]}"
    defn = await api_client.post(
        "/api/v1/reports/definitions",
        headers=headers,
        json={
            "code": defn_code,
            "name": "Dedupe report",
            "report_type": "GENERIC",
        },
    )
    assert defn.status_code == 201, defn.text

    run_dedupe = f"run:{uuid4().hex}"
    run1 = await api_client.post(
        "/api/v1/reports/runs",
        headers=headers,
        json={
            "definition_code": defn_code,
            "dedupe_key": run_dedupe,
        },
    )
    assert run1.status_code == 201, run1.text
    assert run1.json()["created"] is True
    run_id = run1.json()["id"]

    run2 = await api_client.post(
        "/api/v1/reports/runs",
        headers=headers,
        json={
            "definition_code": defn_code,
            "dedupe_key": run_dedupe,
        },
    )
    assert run2.status_code == 200, run2.text
    assert run2.json()["created"] is False
    assert run2.json()["id"] == run_id
