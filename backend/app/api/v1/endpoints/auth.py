"""Public auth endpoints — email/password login and session logout.

Creates hashed UserSession rows. Browser clients receive HttpOnly session
cookie only (no raw session token in JSON). Bearer remains for non-browser
API clients (tests/CI) via Authorization header when ENVIRONMENT=test or
explicit non-browser tooling.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_session_token,
    get_current_user,
    get_db,
    get_password_rotation_user,
)
from app.core.security import (
    decrypt_string,
    generate_session_token,
    get_password_hash,
    verify_password,
)
from app.models.rbac import Role, UserRole
from app.models.user import User, UserMfaMethod, UserSession

router = APIRouter()
logger = logging.getLogger(__name__)

SESSION_DAYS = 7
MFA_SETUP_MINUTES = 10
PASSWORD_RESET_MINUTES = 10
MIN_PASSWORD_LENGTH = 12
RESTRICTED_AUTH_LEVELS = frozenset({"mfa_setup", "password_reset"})
COOKIE_NAME = "session_token"
CSRF_COOKIE = "csrf_token"


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)
    # Optional MFA code when user has an active MFA method enrolled.
    mfa_code: str | None = Field(default=None, max_length=32)


class LoginResponse(BaseModel):
    """Browser-safe login payload — no raw session token."""

    user_id: UUID
    expires_at: datetime
    tenant_id: UUID | None = None
    mfa_required: bool = False
    mfa_enrollment_required: bool = False
    password_change_required: bool = False


PRIVILEGED_MFA_ROLES = {
    "PLATFORM_SUPER_ADMIN",
    "FEDERATION_ADMIN",
    "GYM_OWNER",
    "SUPPORT_PRIVILEGED",
}


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=256)


class PasswordChangeResponse(BaseModel):
    expires_at: datetime
    mfa_enrollment_required: bool = False


class LogoutResponse(BaseModel):
    ok: bool = True


class CsrfResponse(BaseModel):
    csrf_token: str


def _client_meta(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    if ua and len(ua) > 255:
        ua = ua[:255]
    return ip, ua


async def _primary_tenant_id(db: AsyncSession, user_id: UUID) -> UUID | None:
    """First tenant-scoped role for the user, or member.tenant_id for end-user members."""
    from app.models.member import Member

    result = await db.execute(
        select(UserRole.tenant_id)
        .where(
            UserRole.user_id == user_id,
            UserRole.tenant_id.is_not(None),
        )
        .limit(1)
    )
    tid = result.scalar_one_or_none()
    if tid is not None:
        return tid
    m_res = await db.execute(
        select(Member.tenant_id).where(Member.user_id == user_id).limit(1)
    )
    return m_res.scalar_one_or_none()


async def _requires_privileged_mfa(db: AsyncSession, user: User) -> bool:
    if user.is_superuser:
        return True
    result = await db.execute(
        select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user.id,
            Role.name.in_(PRIVILEGED_MFA_ROLES),
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


def resolve_auth_level(
    user: User, *, has_active_mfa: bool, privileged_mfa: bool
) -> str:
    """Decide the assurance level a freshly issued session may carry.

    Enrollment outranks rotation: a privileged account without MFA reaches only
    the enrollment endpoints. Once MFA exists, a provisioned one-time password
    still has to be rotated before the account becomes usable — otherwise
    finishing enrollment would quietly hand out a full session and the rotation
    requirement would be lost.
    """
    if privileged_mfa and not has_active_mfa:
        return "mfa_setup"
    if user.must_change_password:
        return "password_reset"
    return "full"


def session_lifetime(auth_level: str) -> timedelta:
    if auth_level == "mfa_setup":
        return timedelta(minutes=MFA_SETUP_MINUTES)
    if auth_level == "password_reset":
        return timedelta(minutes=PASSWORD_RESET_MINUTES)
    return timedelta(days=SESSION_DAYS)


async def _issue_session(
    *,
    db: AsyncSession,
    request: Request,
    response: Response,
    user: User,
    auth_level: str,
    lifetime: timedelta,
) -> datetime:
    raw_token, token_hash = generate_session_token()
    expires_at = datetime.now(UTC) + lifetime
    ip, ua = _client_meta(request)

    if auth_level in RESTRICTED_AUTH_LEVELS:
        await db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user.id,
                UserSession.auth_level == auth_level,
                UserSession.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )

    db.add(
        UserSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
            ip_address=ip,
            user_agent=ua,
            auth_level=auth_level,
        )
    )
    await db.commit()

    from app.core.config import settings

    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=int(lifetime.total_seconds()),
        path="/",
    )
    return expires_at


@router.get("/csrf", response_model=CsrfResponse)
async def get_csrf(request: Request) -> CsrfResponse:
    """Bootstrap CSRF for cross-origin browsers (JSON body; cookie set by middleware)."""
    token = getattr(request.state, "csrf_token", None) or request.cookies.get(
        CSRF_COOKIE
    )
    if not token:
        # Middleware normally always sets state; fallback for test bypass path
        token = secrets.token_urlsafe(32)
        request.state.csrf_token = token
    return CsrfResponse(csrf_token=token)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate with email/password; create session; set HttpOnly cookie only."""
    email = body.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Generic error for missing / inactive / bad password (no account enumeration).
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    try:
        valid = verify_password(body.password, user.hashed_password)
    except Exception:
        valid = False

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Privileged users without enrollment receive only a short-lived restricted
    # session. It is accepted by the MFA setup endpoints and rejected everywhere
    # else, so password-only authentication never grants application access.
    mfa_row = (
        (
            await db.execute(
                select(UserMfaMethod).where(
                    UserMfaMethod.user_id == user.id,
                    UserMfaMethod.is_active.is_(True),
                )
            )
        )
        .scalars()
        .first()
    )
    privileged_mfa = await _requires_privileged_mfa(db, user)
    tenant_id = await _primary_tenant_id(db, user.id)
    if privileged_mfa and mfa_row is None:
        expires_at = await _issue_session(
            db=db,
            request=request,
            response=response,
            user=user,
            auth_level="mfa_setup",
            lifetime=session_lifetime("mfa_setup"),
        )
        return LoginResponse(
            user_id=user.id,
            expires_at=expires_at,
            tenant_id=tenant_id,
            mfa_required=True,
            mfa_enrollment_required=True,
        )

    if mfa_row is not None:
        code = (body.mfa_code or "").strip()
        if not code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="mfa_required",
            )
        # Brute force protection
        if mfa_row.locked_until and mfa_row.locked_until > datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="mfa_locked_out",
            )

        valid = False

        # Try TOTP
        if mfa_row.encrypted_secret:
            totp_secret = decrypt_string(mfa_row.encrypted_secret)
            totp = pyotp.TOTP(totp_secret)
            if totp.verify(code, valid_window=1):
                valid = True

        # Try Recovery Codes
        if not valid and mfa_row.hashed_recovery_codes:
            for idx, hcode in enumerate(mfa_row.hashed_recovery_codes):
                if verify_password(code, hcode):
                    valid = True
                    # Remove used recovery code
                    mfa_row.hashed_recovery_codes.pop(idx)
                    mfa_row.hashed_recovery_codes = list(mfa_row.hashed_recovery_codes)
                    break

        if not valid:
            mfa_row.failed_attempts = (mfa_row.failed_attempts or 0) + 1
            if mfa_row.failed_attempts >= 5:
                mfa_row.locked_until = datetime.now(UTC) + timedelta(minutes=15)
                mfa_row.failed_attempts = 0
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="mfa_invalid",
            )

        # Reset failed attempts on success
        if mfa_row.failed_attempts or mfa_row.locked_until:
            mfa_row.failed_attempts = 0
            mfa_row.locked_until = None
            await db.commit()

    auth_level = resolve_auth_level(
        user, has_active_mfa=mfa_row is not None, privileged_mfa=privileged_mfa
    )
    expires_at = await _issue_session(
        db=db,
        request=request,
        response=response,
        user=user,
        auth_level=auth_level,
        lifetime=session_lifetime(auth_level),
    )

    return LoginResponse(
        user_id=user.id,
        expires_at=expires_at,
        tenant_id=tenant_id,
        mfa_required=False,
        password_change_required=auth_level == "password_reset",
    )


@router.post("/password", response_model=PasswordChangeResponse)
async def change_password(
    body: PasswordChangeRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(get_password_rotation_user),
    db: AsyncSession = Depends(get_db),
) -> PasswordChangeResponse:
    """Rotate the caller's password and re-issue the session at the right level.

    Reachable from a restricted ``password_reset`` session, which is the only
    thing a provisioned account gets until it rotates the one-time password.
    """
    try:
        current_ok = verify_password(
            body.current_password, current_user.hashed_password
        )
    except Exception:
        current_ok = False
    if not current_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )

    if body.new_password == body.current_password:
        raise HTTPException(status_code=400, detail="password_reused")

    current_user.hashed_password = get_password_hash(body.new_password)
    current_user.must_change_password = False

    # Every session issued against the old password is dead, including this one.
    await db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == current_user.id,
            UserSession.is_revoked.is_(False),
        )
        .values(is_revoked=True)
    )
    await db.flush()

    mfa_row = (
        (
            await db.execute(
                select(UserMfaMethod).where(
                    UserMfaMethod.user_id == current_user.id,
                    UserMfaMethod.is_active.is_(True),
                )
            )
        )
        .scalars()
        .first()
    )
    privileged_mfa = await _requires_privileged_mfa(db, current_user)
    auth_level = resolve_auth_level(
        current_user,
        has_active_mfa=mfa_row is not None,
        privileged_mfa=privileged_mfa,
    )
    expires_at = await _issue_session(
        db=db,
        request=request,
        response=response,
        user=current_user,
        auth_level=auth_level,
        lifetime=session_lifetime(auth_level),
    )
    logger.info(
        "auth.password_rotated user_id=%s next_level=%s",
        current_user.id,
        auth_level,
    )
    return PasswordChangeResponse(
        expires_at=expires_at,
        mfa_enrollment_required=auth_level == "mfa_setup",
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    token: str = Depends(get_current_session_token),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LogoutResponse:
    """Revoke the current session (Bearer or cookie)."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.user_id == current_user.id,
            UserSession.is_revoked.is_(False),
        )
    )
    session = result.scalar_one_or_none()
    if session is not None:
        session.is_revoked = True
        await db.commit()

    response.delete_cookie(key=COOKIE_NAME, path="/")
    return LogoutResponse(ok=True)
