"""Issue and accept hashed account invites.

The raw token is `{tenant_id}.{secret}` so the public accept path can set RLS
before looking the row up. Only the sha256 of the full token is stored.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.invite import (
    ALLOWED_PURPOSES,
    AccountInvite,
)
from app.models.user import User

INVITE_TTL = timedelta(days=7)
MIN_PASSWORD_LENGTH = 12


def hash_invite_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_invite_tenant(raw: str) -> UUID:
    prefix, _sep, _rest = raw.partition(".")
    if not _sep:
        raise ValueError("invalid_invite_token")
    try:
        return UUID(prefix)
    except ValueError as e:
        raise ValueError("invalid_invite_token") from e


class InviteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def issue(
        self,
        tenant_id: UUID,
        user_id: UUID,
        *,
        purpose: str,
    ) -> tuple[AccountInvite, str]:
        if purpose not in ALLOWED_PURPOSES:
            raise ValueError("invalid_invite_purpose")
        raw = f"{tenant_id}.{secrets.token_urlsafe(32)}"
        invite = AccountInvite(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            token_hash=hash_invite_token(raw),
            purpose=purpose,
            expires_at=datetime.now(UTC) + INVITE_TTL,
        )
        self.db.add(invite)
        await self.db.flush()
        return invite, raw

    async def accept(self, raw: str, new_password: str) -> User:
        if len(new_password) < MIN_PASSWORD_LENGTH:
            raise ValueError("password_too_short")
        tenant_id = parse_invite_tenant(raw)
        from sqlalchemy import text

        await self.db.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        digest = hash_invite_token(raw)
        now = datetime.now(UTC)
        invite = (
            await self.db.execute(
                select(AccountInvite).where(
                    AccountInvite.tenant_id == tenant_id,
                    AccountInvite.token_hash == digest,
                )
            )
        ).scalar_one_or_none()
        if invite is None:
            raise ValueError("invite_not_found")
        if invite.accepted_at is not None:
            raise ValueError("invite_already_used")
        if invite.expires_at <= now:
            raise ValueError("invite_expired")

        user = await self.db.get(User, invite.user_id)
        if user is None or not user.is_active:
            raise ValueError("invite_user_inactive")

        user.hashed_password = get_password_hash(new_password)
        user.must_change_password = False
        invite.accepted_at = now
        await self.db.flush()
        return user
