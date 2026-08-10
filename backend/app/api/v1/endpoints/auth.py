"""Public auth endpoints — email/password login and session logout.

Creates hashed UserSession rows. Browser clients receive HttpOnly session
cookie only (no raw session token in JSON). Bearer remains for non-browser
API clients (tests/CI) via Authorization header when ENVIRONMENT=test or
explicit non-browser tooling.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_session_token, get_current_user, get_db
from app.core.security import generate_session_token, verify_password
from app.models.rbac import UserRole
from app.models.user import User, UserMfaMethod, UserSession

router = APIRouter()

SESSION_DAYS = 7
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
    """First tenant-scoped role for the user (Admin Web needs X-Tenant-ID)."""
    result = await db.execute(
        select(UserRole.tenant_id)
        .where(
            UserRole.user_id == user_id,
            UserRole.tenant_id.is_not(None),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


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

    # MFA gate: active enrollment requires mfa_code before session cookie is issued.
    # Full TOTP against encrypted_secret is follow-up; enrolled methods refuse empty codes.
    mfa_row = (
        await db.execute(
            select(UserMfaMethod).where(
                UserMfaMethod.user_id == user.id,
                UserMfaMethod.is_active.is_(True),
            )
        )
    ).scalars().first()
    if mfa_row is not None:
        code = (body.mfa_code or "").strip()
        if not code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="mfa_required",
            )
        # Temporary verifier until TOTP: if provider_id is set, code must match it.
        expected = (mfa_row.provider_id or "").strip()
        if expected and not hmac.compare_digest(code, expected):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="mfa_invalid",
            )

    raw_token, token_hash = generate_session_token()
    expires_at = datetime.now(UTC) + timedelta(days=SESSION_DAYS)
    ip, ua = _client_meta(request)

    db.add(
        UserSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
            ip_address=ip,
            user_agent=ua,
        )
    )
    await db.commit()

    tenant_id = await _primary_tenant_id(db, user.id)

    from app.core.config import settings

    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )

    return LoginResponse(
        user_id=user.id,
        expires_at=expires_at,
        tenant_id=tenant_id,
        mfa_required=False,
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
