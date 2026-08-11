"""Phase 13 QR & Access engine — issue, rotate, validate (flush-only)."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.qr_crypto import (
    DEFAULT_ALGORITHM,
    QrCryptoError,
    build_payload,
    new_local_hmac_ref,
    sign_payload,
    verify_and_decode,
)
from app.models.access import (
    AccessAttempt,
    AccessStatus,
    Checkin,
    KeyStatus,
    QrJtiReplay,
    SigningKey,
)
from app.models.member import Member
from app.services.entitlement import EntitlementService

DEFAULT_QR_TTL_SECONDS = 60
DEFAULT_AUD = "access"


@dataclass
class IssueQrResult:
    token: str
    kid: str
    jti: str
    credential_id: str
    exp: datetime
    iat: datetime


@dataclass
class ValidateQrResult:
    granted: bool
    reason: str | None
    member_id: UUID | None = None
    jti: str | None = None
    attempt_id: UUID | None = None
    checkin_id: UUID | None = None
    remaining: int | None = None


class AccessService:
    """QR credential issue / key rotation / validate + access log."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ keys
    async def get_active_key(self, tenant_id: UUID) -> SigningKey | None:
        result = await self.db.execute(
            select(SigningKey).where(
                SigningKey.tenant_id == tenant_id,
                SigningKey.status == KeyStatus.ACTIVE,
            )
        )
        return result.scalars().first()

    async def list_keys(self, tenant_id: UUID) -> list[SigningKey]:
        result = await self.db.execute(
            select(SigningKey)
            .where(SigningKey.tenant_id == tenant_id)
            .order_by(SigningKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def ensure_active_key(self, tenant_id: UUID) -> SigningKey:
        key = await self.get_active_key(tenant_id)
        if key is not None:
            return key
        return await self._create_active_key(tenant_id)

    async def rotate_signing_key(self, tenant_id: UUID) -> SigningKey:
        """ACTIVE → VERIFY_ONLY for current; mint new ACTIVE kid."""
        current = await self.get_active_key(tenant_id)
        if current is not None:
            current.status = KeyStatus.VERIFY_ONLY
            await self.db.flush()
        return await self._create_active_key(tenant_id)

    async def revoke_key(self, tenant_id: UUID, kid: str) -> SigningKey | None:
        result = await self.db.execute(
            select(SigningKey).where(
                SigningKey.tenant_id == tenant_id,
                SigningKey.kid == kid,
            )
        )
        key = result.scalars().first()
        if key is None:
            return None
        key.status = KeyStatus.REVOKED
        await self.db.flush()
        return key

    async def _create_active_key(self, tenant_id: UUID) -> SigningKey:
        kid = f"qr-{datetime.now(UTC).strftime('%Y%m')}-{secrets.token_hex(3)}"
        key = SigningKey(
            tenant_id=tenant_id,
            kid=kid,
            status=KeyStatus.ACTIVE,
            algorithm=DEFAULT_ALGORITHM,
            key_material=new_local_hmac_ref(),
        )
        self.db.add(key)
        await self.db.flush()
        return key

    # ------------------------------------------------------------------ issue
    async def issue_qr_token(
        self,
        tenant_id: UUID,
        member_id: UUID,
        *,
        ttl_seconds: int = DEFAULT_QR_TTL_SECONDS,
        aud: str = DEFAULT_AUD,
        now: datetime | None = None,
    ) -> IssueQrResult:
        if ttl_seconds < 15 or ttl_seconds > 600:
            raise ValueError("ttl_seconds must be between 15 and 600")

        member = await self.db.get(Member, member_id)
        if member is None or member.tenant_id != tenant_id:
            raise ValueError("member_not_found")

        key = await self.ensure_active_key(tenant_id)
        now = now or datetime.now(UTC)
        exp = now + timedelta(seconds=ttl_seconds)
        jti = secrets.token_urlsafe(16)
        credential_id = str(uuid4())
        payload = build_payload(
            kid=key.kid,
            credential_id=credential_id,
            jti=jti,
            iat=now,
            exp=exp,
            aud=aud,
            tenant_id=tenant_id,
            member_id=member_id,
        )
        token = sign_payload(payload, key.key_material)
        return IssueQrResult(
            token=token,
            kid=key.kid,
            jti=jti,
            credential_id=credential_id,
            exp=exp,
            iat=now,
        )

    # ---------------------------------------------------------------- validate
    async def validate_qr(
        self,
        tenant_id: UUID,
        token: str,
        *,
        device_id: UUID | None = None,
        location_id: UUID | None = None,
        action: str = "GYM_ENTRY",
        consume: bool = False,
        quantity: int = 1,
        aud: str = DEFAULT_AUD,
        now: datetime | None = None,
        require_entitlement: bool = True,
    ) -> ValidateQrResult:
        now = now or datetime.now(UTC)

        kid = self._peek_kid(token)
        if kid is None:
            return await self._deny(
                tenant_id, None, None, "malformed_token", device_id=device_id
            )

        result = await self.db.execute(
            select(SigningKey).where(
                SigningKey.tenant_id == tenant_id,
                SigningKey.kid == kid,
            )
        )
        key = result.scalars().first()
        if key is None:
            return await self._deny(
                tenant_id, None, None, "unknown_kid", device_id=device_id
            )
        if key.status == KeyStatus.REVOKED:
            return await self._deny(
                tenant_id, None, None, "key_revoked", device_id=device_id
            )
        if key.status not in (KeyStatus.ACTIVE, KeyStatus.VERIFY_ONLY):
            return await self._deny(
                tenant_id, None, None, "key_not_usable", device_id=device_id
            )

        try:
            payload = verify_and_decode(
                token,
                key.key_material,
                expected_tenant_id=tenant_id,
                expected_aud=aud,
                now=now,
            )
        except QrCryptoError as e:
            return await self._deny(
                tenant_id, None, None, str(e), device_id=device_id
            )

        member_id = UUID(str(payload["member_id"]))
        jti = str(payload["jti"])
        credential_id = str(payload["credential_id"])
        exp = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)

        # Replay protection — nested savepoint so IntegrityError is isolated
        replay = QrJtiReplay(
            tenant_id=tenant_id,
            jti=jti,
            member_id=member_id,
            credential_id=credential_id,
            expires_at=exp,
            consumed_at=now,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(replay)
                await self.db.flush()
        except IntegrityError:
            return await self._deny(
                tenant_id, member_id, jti, "replay", device_id=device_id
            )

        remaining: int | None = None
        if require_entitlement:
            if consume:
                ent = await EntitlementService.consume_access(
                    self.db,
                    tenant_id,
                    member_id,
                    action,
                    f"qr-consume:{jti}",
                    quantity=quantity,
                )
            else:
                ent = await EntitlementService.check_access(
                    self.db,
                    tenant_id,
                    member_id,
                    action,
                    quantity=quantity,
                )
            remaining = ent.get("remaining")
            if not ent.get("granted"):
                attempt = await self._record_attempt(
                    tenant_id,
                    member_id=member_id,
                    jti=jti,
                    status=AccessStatus.DENIED,
                    reason=ent.get("reason") or "entitlement_denied",
                    device_id=device_id,
                )
                return ValidateQrResult(
                    granted=False,
                    reason=ent.get("reason") or "entitlement_denied",
                    member_id=member_id,
                    jti=jti,
                    attempt_id=attempt.id,
                    remaining=remaining,
                )

        attempt = await self._record_attempt(
            tenant_id,
            member_id=member_id,
            jti=jti,
            status=AccessStatus.GRANTED,
            reason=None,
            device_id=device_id,
        )
        checkin_id = None
        if location_id is None:
            from app.models.location import Location as LocationModel
            res_loc = await self.db.execute(select(LocationModel).where(LocationModel.tenant_id == tenant_id))
            loc = res_loc.scalars().first()
            if loc:
                location_id = loc.id

        if location_id is not None:
            checkin = Checkin(
                tenant_id=tenant_id,
                member_id=member_id,
                location_id=location_id,
                device_id=device_id,
                checkin_time=now,
            )
            self.db.add(checkin)
            await self.db.flush()
            checkin_id = checkin.id

        return ValidateQrResult(
            granted=True,
            reason=None,
            member_id=member_id,
            jti=jti,
            attempt_id=attempt.id,
            checkin_id=checkin_id,
            remaining=remaining,
        )

    @staticmethod
    def _peek_kid(token: str) -> str | None:
        import base64
        import json

        try:
            body_b64 = token.split(".", 1)[0]
            pad = "=" * (-len(body_b64) % 4)
            peek = json.loads(base64.urlsafe_b64decode(body_b64 + pad))
            kid = peek.get("kid")
            return str(kid) if kid else None
        except Exception:
            return None


    async def _deny(
        self,
        tenant_id: UUID,
        member_id: UUID | None,
        jti: str | None,
        reason: str,
        *,
        device_id: UUID | None = None,
    ) -> ValidateQrResult:
        attempt = await self._record_attempt(
            tenant_id,
            member_id=member_id,
            jti=jti,
            status=AccessStatus.DENIED,
            reason=reason,
            device_id=device_id,
        )
        return ValidateQrResult(
            granted=False,
            reason=reason,
            member_id=member_id,
            jti=jti,
            attempt_id=attempt.id,
        )

    async def _record_attempt(
        self,
        tenant_id: UUID,
        *,
        member_id: UUID | None,
        jti: str | None,
        status: AccessStatus,
        reason: str | None,
        device_id: UUID | None,
    ) -> AccessAttempt:
        attempt = AccessAttempt(
            tenant_id=tenant_id,
            member_id=member_id,
            device_id=device_id,
            status=status,
            denial_reason=reason,
            jti=jti,
            method="QR_SCAN",
            timestamp=datetime.now(UTC),
        )
        self.db.add(attempt)
        await self.db.flush()
        return attempt
