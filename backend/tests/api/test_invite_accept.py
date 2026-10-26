"""Hashed invite tokens are one-shot and set the password."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.invite import AccountInvite
from tests.api.test_staff_account_provisioning import (
    _create_account,
    _headers,
    _tenant_with_actor,
)
from tests.api.test_staff_account_provisioning import (
    api_client as _staff_api_client,
)

api_client = _staff_api_client


@pytest.mark.asyncio
async def test_staff_invite_accept_sets_password_and_burns_token(api_client, pg_engine):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    email, res = await _create_account(api_client, tenant_id, token)
    assert res.status_code == 201, res.text
    invite = res.json()["invite_token"]
    assert invite
    assert str(tenant_id) in invite

    accepted = await api_client.post(
        "/api/v1/auth/invite/accept",
        json={"token": invite, "new_password": "InvitePassphrase9!"},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["email"] == email

    replay = await api_client.post(
        "/api/v1/auth/invite/accept",
        json={"token": invite, "new_password": "InvitePassphrase9!"},
    )
    assert replay.status_code == 409

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "InvitePassphrase9!"},
    )
    assert login.status_code == 200, login.text


@pytest.mark.asyncio
async def test_invite_accept_rejects_unknown_token(api_client, pg_engine):
    tenant_id, _token = await _tenant_with_actor(pg_engine)
    res = await api_client.post(
        "/api/v1/auth/invite/accept",
        json={
            "token": f"{tenant_id}.{'a' * 40}",
            "new_password": "InvitePassphrase9!",
        },
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_expired_invite_is_rejected(api_client, pg_engine):
    tenant_id, token = await _tenant_with_actor(pg_engine)
    _email, res = await _create_account(api_client, tenant_id, token)
    assert res.status_code == 201, res.text
    invite = res.json()["invite_token"]

    from sqlalchemy import text

    from app.api.deps import current_tenant_id_var

    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    token_ctx = current_tenant_id_var.set(tenant_id)
    try:
        async with maker() as db:
            await db.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": str(tenant_id)},
            )
            row = (await db.execute(select(AccountInvite))).scalars().first()
            assert row is not None
            row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
            await db.commit()
    finally:
        current_tenant_id_var.reset(token_ctx)

    expired = await api_client.post(
        "/api/v1/auth/invite/accept",
        json={"token": invite, "new_password": "InvitePassphrase9!"},
        headers=_headers(token, tenant_id),
    )
    assert expired.status_code == 400
    assert expired.json()["detail"] == "invite_expired"
