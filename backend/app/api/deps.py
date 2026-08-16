import contextvars
from datetime import UTC
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_session_token_from_cookie
from app.core.session_policy import (
    PRIVILEGED_IDLE,
    PRIVILEGED_ROLE_NAMES,
    STEP_UP_MAX_AGE,
    STEP_UP_REQUIRED,
)
from app.db.session import get_db
from app.models.rbac import Role, UserRole
from app.models.user import User, UserSession

# Context variable to hold the current tenant ID for the request
current_tenant_id_var: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    "current_tenant_id", default=None
)


def get_current_session_token(request: Request) -> str:
    """
    Dependency that enforces authentication via Secure HttpOnly cookie.
    """
    token = get_session_token_from_cookie(request)

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


async def get_current_user(
    token: str = Depends(get_current_session_token), db: AsyncSession = Depends(get_db)
) -> User:
    """Retrieve a fully authenticated user from the session token."""
    user, _session = await _get_user_and_session(
        token, db, allowed_auth_levels={"full"}
    )
    return user


async def require_recent_step_up(
    token: str = Depends(get_current_session_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require a TOTP step-up within STEP_UP_MAX_AGE for sensitive writes."""
    from datetime import datetime

    user, session = await _get_user_and_session(
        token, db, allowed_auth_levels={"full"}
    )
    from app.models.user import UserMfaMethod

    enrolled = (
        await db.execute(
            select(UserMfaMethod).where(
                UserMfaMethod.user_id == user.id,
                UserMfaMethod.is_active.is_(True),
            )
        )
    ).scalars().first()
    if enrolled is None:
        return user
    now = datetime.now(UTC)
    stamped = session.last_step_up_at
    if stamped is None or stamped.tzinfo is None:
        fresh = False
    else:
        fresh = now - stamped <= STEP_UP_MAX_AGE
    if not fresh:
        raise HTTPException(status_code=403, detail=STEP_UP_REQUIRED)
    return user


async def _get_user_for_session(
    token: str, db: AsyncSession, *, allowed_auth_levels: set[str]
) -> User:
    user, _session = await _get_user_and_session(
        token, db, allowed_auth_levels=allowed_auth_levels
    )
    return user


def _is_privileged_principal(user: User) -> bool:
    if user.is_superuser:
        return True
    for user_role in user.user_roles:
        role = user_role.role
        if role is not None and role.name in PRIVILEGED_ROLE_NAMES:
            return True
    return False


async def _get_user_and_session(
    token: str, db: AsyncSession, *, allowed_auth_levels: set[str]
) -> tuple[User, UserSession]:
    """Resolve a server session and enforce its authentication assurance."""
    import hashlib
    from datetime import datetime

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(UTC)

    result = await db.execute(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.is_revoked == False,
            UserSession.expires_at > now,
            UserSession.auth_level.in_(allowed_auth_levels),
        )
    )
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    from sqlalchemy.orm import selectinload

    result_user = await db.execute(
        select(User)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions)
        )
        .where(User.id == session.user_id)
    )
    user = result_user.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")

    prev_seen = session.last_seen_at
    if (
        prev_seen is not None
        and prev_seen.tzinfo is not None
        and _is_privileged_principal(user)
        and now - prev_seen > PRIVILEGED_IDLE
        and session.auth_level == "full"
    ):
        session.is_revoked = True
        await db.commit()
        raise HTTPException(status_code=401, detail="session_idle")
    session.last_seen_at = now
    await db.commit()

    return user, session


async def get_mfa_enrollment_user(
    token: str = Depends(get_current_session_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Allow a full session or a short-lived MFA-enrollment-only session."""
    return await _get_user_for_session(
        token, db, allowed_auth_levels={"full", "mfa_setup"}
    )


async def get_password_rotation_user(
    token: str = Depends(get_current_session_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Allow a full session or a short-lived password-rotation-only session."""
    return await _get_user_for_session(
        token, db, allowed_auth_levels={"full", "password_reset"}
    )


async def _audit_superuser_tenant_access(
    db: AsyncSession, user: User, tenant_id: UUID
) -> None:
    """Record a superuser asserting a tenant it holds no UserRole for.

    ``is_superuser`` lets a caller name any tenant in X-Tenant-ID. That is a
    deliberate operational capability, but it used to leave no trace and was
    indistinguishable from ordinary tenant traffic in the logs.
    """
    from app.models.audit import AuditEvent

    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id, UserRole.tenant_id == tenant_id
        )
    )
    if result.scalars().first() is not None:
        # Genuine member of the tenant — not impersonation.
        return

    db.add(
        AuditEvent(
            tenant_id=tenant_id,
            user_id=user.id,
            action="superuser.tenant_impersonation",
            resource_type="tenant",
            resource_id=tenant_id,
            new_state={"email": user.email},
        )
    )
    await db.flush()


async def _verify_tenant_status(db: AsyncSession, tenant_id: UUID) -> None:
    from app.models.tenant import Tenant, TenantStatus

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalars().first()
    if tenant:
        if tenant.status == TenantStatus.SUSPENDED:
            raise HTTPException(status_code=403, detail="Tenant is suspended")
        if tenant.status == TenantStatus.CLOSED:
            raise HTTPException(status_code=403, detail="Tenant is closed")


async def get_tenant_id(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Dependency to extract and validate the X-Tenant-ID header."""
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid X-Tenant-ID header format. Must be a UUID."
        )

    # Temporarily set the RLS context so we can read the UserRole for this tenant
    await db.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )

    # 1. Verify user belongs to the requested tenant via UserRole
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id, UserRole.tenant_id == tenant_id
        )
    )
    user_role = result.scalars().first()

    if user_role:
        await _verify_tenant_status(db, tenant_id)
        current_tenant_id_var.set(tenant_id)
        return tenant_id

    # 2. If not a member, check if superuser with active Break-Glass session
    if user.is_superuser:
        from app.services.break_glass import BreakGlassService

        bg_service = BreakGlassService(db)
        active_bg = await bg_service.check_active_session(
            actor_id=user.id, tenant_id=tenant_id
        )
        if not active_bg:
            await db.execute(text("SET LOCAL app.current_tenant_id = '';"))
            raise HTTPException(
                status_code=403,
                detail="Bu işletmeye erişmek için aktif bir acil durum (break-glass) oturumu gereklidir.",
            )

        # Active break-glass session exists: audit, verify status, and allow
        await _audit_superuser_tenant_access(db, user, tenant_id)
        await _verify_tenant_status(db, tenant_id)
        current_tenant_id_var.set(tenant_id)
        return tenant_id

    # 3. Non-superuser and not a member: forbid
    await db.execute(text("SET LOCAL app.current_tenant_id = '';"))
    raise HTTPException(
        status_code=403, detail="User does not have access to this tenant"
    )


async def get_optional_tenant_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UUID | None:
    """Same checks as get_tenant_id, but the header may be absent.

    Federation and platform principals hold no tenant-scoped UserRole, so a
    hard tenant requirement would make them unable to answer even "who am I".
    When the header is present the full membership check still applies — this
    relaxes the requirement, not the verification.
    """
    if x_tenant_id is None:
        return None
    return await get_tenant_id(x_tenant_id=x_tenant_id, user=user, db=db)


class FederationScope:
    """Which organizations a federation-level caller may read across.

    ``org_ids is None`` means platform scope (every organization). A list means
    exactly those organizations; an empty list means nothing is readable.
    """

    def __init__(self, user: User, org_ids: list[UUID] | None):
        self.user = user
        self.org_ids = org_ids

    @property
    def is_platform(self) -> bool:
        return self.org_ids is None


FEDERATION_ROLE_NAMES = {
    "FEDERATION_ADMIN",
    "FEDERATION_ANALYST",
    "FEDERATION_SUPPORT",
}


async def get_federation_scope(
    user: User = Depends(get_current_user),
) -> FederationScope:
    """Authorize a cross-tenant read and derive its organization scope.

    Deliberately does not depend on ``get_tenant_id``: federation reads address
    no single tenant, so requiring X-Tenant-ID would be meaningless. Scope comes
    from the caller's own role assignments, never from a client-supplied value.
    """
    if user.is_superuser:
        return FederationScope(user, None)

    org_ids: list[UUID] = []
    for user_role in user.user_roles:
        role = user_role.role
        if role is None:
            continue
        if (
            user_role.tenant_id is None
            and user_role.organization_id is None
            and role.name == "PLATFORM_SUPER_ADMIN"
        ):
            return FederationScope(user, None)
        if user_role.organization_id is not None and role.name in FEDERATION_ROLE_NAMES:
            org_ids.append(user_role.organization_id)

    if not org_ids:
        raise HTTPException(
            status_code=403, detail="Not a platform or federation principal"
        )
    return FederationScope(user, org_ids)


async def _verify_device_signature(
    request: Request, db: AsyncSession, session, tenant_id: UUID
) -> None:
    """Reject a device request that does not prove possession of the signing secret.

    The session token alone (a cookie, and therefore stealable off the device or
    replayable by anything that can read it) is deliberately not sufficient: the
    caller must also sign the request with the per-session secret handed out at
    ``POST /devices/auth``. The nonce claim then makes each signed request
    single-use, so capturing one on the wire buys nothing either.
    """
    from datetime import datetime, timedelta

    from sqlalchemy import delete
    from sqlalchemy.exc import IntegrityError

    from app.core.device_auth import (
        MAX_CLOCK_SKEW_SECONDS,
        MAX_NONCE_LENGTH,
        MIN_NONCE_LENGTH,
        NONCE_HEADER,
        NONCE_RETENTION_SECONDS,
        SIGNATURE_HEADER,
        TIMESTAMP_HEADER,
        verify_signature,
    )
    from app.core.qr_crypto import QrCryptoError
    from app.models.access import DeviceNonce

    if not session.signing_key_material:
        # Session predates request signing (or was issued without material).
        # Fail closed and make the device re-authenticate rather than silently
        # falling back to cookie-only trust.
        raise HTTPException(status_code=401, detail="device_session_unsigned")

    signature = request.headers.get(SIGNATURE_HEADER)
    timestamp = request.headers.get(TIMESTAMP_HEADER)
    nonce = request.headers.get(NONCE_HEADER)

    if not signature or not timestamp or not nonce:
        raise HTTPException(status_code=401, detail="device_signature_missing")

    if not (MIN_NONCE_LENGTH <= len(nonce) <= MAX_NONCE_LENGTH):
        raise HTTPException(status_code=401, detail="device_nonce_invalid")

    try:
        sent_at = int(timestamp)
    except ValueError:
        raise HTTPException(
            status_code=401, detail="device_timestamp_invalid"
        ) from None

    now = datetime.now(UTC)
    if abs(int(now.timestamp()) - sent_at) > MAX_CLOCK_SKEW_SECONDS:
        raise HTTPException(status_code=401, detail="device_timestamp_skew")

    body = await request.body()
    try:
        ok = verify_signature(
            session.signing_key_material,
            signature,
            request.method,
            request.url.path,
            timestamp,
            nonce,
            body,
        )
    except QrCryptoError:
        raise HTTPException(
            status_code=401, detail="device_signature_invalid"
        ) from None
    if not ok:
        raise HTTPException(status_code=401, detail="device_signature_invalid")

    # Signature is valid — only now is the nonce worth spending.
    await db.execute(delete(DeviceNonce).where(DeviceNonce.expires_at < now))
    try:
        async with db.begin_nested():
            db.add(
                DeviceNonce(
                    tenant_id=tenant_id,
                    device_session_id=session.id,
                    nonce=nonce,
                    expires_at=now + timedelta(seconds=NONCE_RETENTION_SECONDS),
                )
            )
            await db.flush()
    except IntegrityError:
        raise HTTPException(status_code=401, detail="device_nonce_replay") from None


async def get_current_device(request: Request, db: AsyncSession = Depends(get_db)):
    import hashlib

    from app.models.access import Device, DeviceSession, DeviceStatus

    token = request.cookies.get("device_session")
    auth_header = request.headers.get("Authorization")
    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated as device")

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    from datetime import datetime

    result = await db.execute(
        select(DeviceSession).where(
            DeviceSession.token_hash == token_hash,
            DeviceSession.is_revoked == False,
            DeviceSession.expires_at > datetime.now(UTC),
        )
    )
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired device session")

    # The session row is the bootstrap credential (device_sessions carries no RLS
    # policy for exactly this reason); every read after it happens under tenant
    # context, so `devices` and `device_nonces` stay RLS-protected like any other
    # tenant-owned table.
    current_tenant_id_var.set(session.tenant_id)
    await db.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(session.tenant_id)},
    )
    await _verify_tenant_status(db, session.tenant_id)

    result_device = await db.execute(
        select(Device).where(
            Device.id == session.device_id, Device.tenant_id == session.tenant_id
        )
    )
    device = result_device.scalars().first()

    if not device or not device.is_active or device.status == DeviceStatus.OFFLINE:
        # If device was marked offline by revocation or something else
        raise HTTPException(status_code=401, detail="Device inactive or offline")

    await _verify_device_signature(request, db, session, device.tenant_id)

    return device
