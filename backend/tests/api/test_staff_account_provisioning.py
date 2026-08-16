"""Provisioned staff accounts — creation, one-time password, forced rotation.

An administrator can create a login for a colleague. The generated password is
shown once and must be rotated before the account can do anything, so these
tests care less about the happy path than about the restricted window between
"account exists" and "password rotated".
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pyotp
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

OWNER_PERMS = ["staff:read", "staff:write"]
READER_PERMS = ["staff:read"]


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


async def _actor(
    db: AsyncSession, *, tenant_id, perm_names: list[str]
) -> tuple[User, str]:
    """A user holding a private role, so sibling tests cannot be affected."""
    raw = f"tok_{uuid4().hex}"
    user = User(
        email=f"actor-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    role = Role(
        name=f"PROVISIONER-{uuid4().hex[:8]}",
        description="private test role",
        permissions=await _ensure_perms(db, perm_names),
    )
    db.add(role)
    await db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant_id))
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            auth_level="full",
        )
    )
    await db.flush()
    return user, raw


async def _tenant_with_actor(pg_engine, perm_names: list[str] = OWNER_PERMS):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Prov Org", domain=f"prov-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Prov Tenant",
            organization_id=org.id,
            location_code=f"PV-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        _, token = await _actor(db, tenant_id=tenant.id, perm_names=perm_names)
        await db.commit()
        return tenant.id, token


def _headers(token: str, tenant_id) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
    }


async def _create_account(api_client, tenant_id, token, *, email=None, role="STAFF"):
    email = email or f"new-{uuid4().hex[:8]}@example.com"
    res = await api_client.post(
        "/api/v1/staff/accounts",
        headers=_headers(token, tenant_id),
        json={"email": email, "role": role},
    )
    return email, res


async def _accept_invite(api_client, invite_token: str, password: str) -> None:
    res = await api_client.post(
        "/api/v1/auth/invite/accept",
        json={"token": invite_token, "new_password": password},
    )
    assert res.status_code == 200, res.text


async def _session_after_first_login(
    api_client, email: str, otp: str
) -> tuple[str, str | None]:
    """Walk a provisioned account through MFA so password rotation is reachable.

    FRONT_DESK (the default STAFF mapping) is privileged-MFA, so enrollment
    outranks rotation. Tests that hit /auth/password need the post-MFA
    password_reset session.
    """
    login = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": otp}
    )
    assert login.status_code == 200, login.text
    totp_secret: str | None = None
    if login.json().get("mfa_enrollment_required"):
        setup = await api_client.post("/api/v1/auth/mfa/setup")
        assert setup.status_code == 200, setup.text
        totp_secret = setup.json()["secret"]
        code = pyotp.TOTP(totp_secret).now()
        verify = await api_client.post(
            "/api/v1/auth/mfa/verify", json={"code": code}
        )
        assert verify.status_code == 200, verify.text
    return api_client.cookies["session_token"], totp_secret


@pytest.mark.asyncio
async def test_created_account_is_linked_and_returns_a_one_time_password(
    api_client, pg_engine
):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, res = await _create_account(api_client, tenant_id, token)

    assert res.status_code == 201, res.text
    body = res.json()
    assert body["email"] == email
    assert body["staff"]["tenant_id"] == str(tenant_id)
    assert body["staff"]["user_id"] == body["user_id"]
    assert body["staff"]["email"] == email
    assert "one_time_password" not in body
    assert body["invite_token"]
    assert str(tenant_id) in body["invite_token"]
    # The invite is a credential in transit; it must not be cached on the way.
    assert res.headers["cache-control"] == "no-store"

    from app.models.notification import NotificationDelivery
    from app.models.rbac import Role, UserRole

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        delivery = (
            await db.execute(
                select(NotificationDelivery).where(
                    NotificationDelivery.tenant_id == tenant_id,
                    NotificationDelivery.recipient_user_id == body["user_id"],
                )
            )
        ).scalar_one_or_none()
        assert delivery is not None
        assert delivery.channel == "EMAIL"
        assert body["invite_token"] in (delivery.body or "")
        assert "Tek kullanımlık parola" not in (delivery.body or "")
        assert delivery.context.get("kind") == "staff_account_created"
        role = (
            await db.execute(select(Role).where(Role.name == "FRONT_DESK"))
        ).scalar_one()
        link = (
            await db.execute(
                select(UserRole).where(
                    UserRole.user_id == body["user_id"],
                    UserRole.role_id == role.id,
                    UserRole.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert link is not None


@pytest.mark.asyncio
async def test_provisioned_account_cannot_use_the_app_before_rotating(
    api_client, pg_engine
):
    """The whole point of the flag: a one-time password is not app access."""
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, res = await _create_account(api_client, tenant_id, token)
    assert res.status_code == 201, res.text
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "InvitePassphrase9!"},
    )
    assert login.status_code == 401


@pytest.mark.asyncio
async def test_rotation_opens_the_account_and_burns_the_old_password(
    api_client, pg_engine
):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, res = await _create_account(api_client, tenant_id, token)
    otp = "InvitePassphrase9!"
    await _accept_invite(api_client, res.json()["invite_token"], otp)

    restricted, totp_secret = await _session_after_first_login(api_client, email, otp)

    new_password = "RotatedPassphrase9!"
    rotate = await api_client.post(
        "/api/v1/auth/password",
        headers={"Authorization": f"Bearer {restricted}"},
        json={"current_password": otp, "new_password": new_password},
    )
    assert rotate.status_code == 200, rotate.text
    assert rotate.json()["mfa_enrollment_required"] is False

    rotated = rotate.cookies["session_token"]
    allowed = await api_client.get(
        "/api/v1/me/session", headers={"Authorization": f"Bearer {rotated}"}
    )
    assert allowed.status_code == 200

    # The session that carried the old password is dead, not merely upgraded.
    # The cookie jar now holds the rotated token and the cookie outranks the
    # Bearer header, so it has to be cleared for the old token to be the one
    # actually under test.
    api_client.cookies.clear()
    stale = await api_client.get(
        "/api/v1/me/session", headers={"Authorization": f"Bearer {restricted}"}
    )
    assert stale.status_code == 401

    # And the one-time password cannot be used a second time.
    replay = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": otp}
    )
    assert replay.status_code == 401

    fresh_payload = {"email": email, "password": new_password}
    if totp_secret:
        fresh_payload["mfa_code"] = pyotp.TOTP(totp_secret).now()
    fresh = await api_client.post("/api/v1/auth/login", json=fresh_payload)
    assert fresh.status_code == 200
    assert fresh.json()["password_change_required"] is False


@pytest.mark.asyncio
async def test_rotation_refuses_a_wrong_current_password(api_client, pg_engine):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, res = await _create_account(api_client, tenant_id, token)
    otp = "InvitePassphrase9!"
    await _accept_invite(api_client, res.json()["invite_token"], otp)
    restricted, _ = await _session_after_first_login(api_client, email, otp)

    bad = await api_client.post(
        "/api/v1/auth/password",
        headers={"Authorization": f"Bearer {restricted}"},
        json={
            "current_password": "not-the-password",
            "new_password": "RotatedPassphrase9!",
        },
    )
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_rotation_refuses_reusing_the_same_password(api_client, pg_engine):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, res = await _create_account(api_client, tenant_id, token)
    otp = "InvitePassphrase9!"
    await _accept_invite(api_client, res.json()["invite_token"], otp)
    restricted, _ = await _session_after_first_login(api_client, email, otp)

    reused = await api_client.post(
        "/api/v1/auth/password",
        headers={"Authorization": f"Bearer {restricted}"},
        json={"current_password": otp, "new_password": otp},
    )
    assert reused.status_code == 400
    assert reused.json()["detail"] == "password_reused"


@pytest.mark.asyncio
async def test_short_new_password_is_rejected(api_client, pg_engine):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, res = await _create_account(api_client, tenant_id, token)
    otp = "InvitePassphrase9!"
    await _accept_invite(api_client, res.json()["invite_token"], otp)
    restricted, _ = await _session_after_first_login(api_client, email, otp)

    short = await api_client.post(
        "/api/v1/auth/password",
        headers={"Authorization": f"Bearer {restricted}"},
        json={"current_password": otp, "new_password": "short1!"},
    )
    assert short.status_code == 422


@pytest.mark.asyncio
async def test_existing_email_conflicts_instead_of_rebinding(api_client, pg_engine):
    """Silently attaching someone else's login to your tenant is a boundary bug."""
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, first = await _create_account(api_client, tenant_id, token)
    assert first.status_code == 201

    _, second = await _create_account(api_client, tenant_id, token, email=email)
    assert second.status_code == 400
    assert second.json()["detail"] == "email_already_registered"


@pytest.mark.asyncio
async def test_email_case_does_not_create_a_duplicate(api_client, pg_engine):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, first = await _create_account(api_client, tenant_id, token)
    assert first.status_code == 201

    _, second = await _create_account(api_client, tenant_id, token, email=email.upper())
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_caller_without_staff_write_is_refused(api_client, pg_engine):
    tenant_id, token = await _tenant_with_actor(pg_engine, perm_names=READER_PERMS)
    _, res = await _create_account(api_client, tenant_id, token)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_unknown_role_is_rejected_before_the_account_exists(
    api_client, pg_engine, pg_session_maker
):
    """A rejected role must not leave an orphaned login behind."""
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, res = await _create_account(
        api_client, tenant_id, token, role="SUPREME_LEADER"
    )
    assert res.status_code == 400

    async with pg_session_maker() as db:
        orphan = (
            await db.execute(select(User).where(User.email == email.lower()))
        ).scalar_one_or_none()
    assert orphan is None


@pytest.mark.asyncio
async def test_staff_list_includes_login_email(api_client, pg_engine):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, created = await _create_account(api_client, tenant_id, token, role="TRAINER")
    assert created.status_code == 201, created.text

    listed = await api_client.get("/api/v1/staff", headers=_headers(token, tenant_id))
    assert listed.status_code == 200, listed.text
    rows = listed.json()
    match = next(row for row in rows if row["email"] == email)
    assert match["role"] == "TRAINER"
    assert match["user_id"] == created.json()["user_id"]
