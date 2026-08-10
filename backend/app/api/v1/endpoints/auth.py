"""Public auth endpoints — email/password login and session logout.

Creates hashed UserSession rows (same model as seed_demo / Bearer auth).
Returns raw token for Admin Web localStorage; also sets HttpOnly cookie.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_session_token, get_current_user, get_db
from app.core.security import (
    generate_session_token,
    verify_password,
)
from app.models.rbac import UserRole
from app.models.user import User, UserSession

router = APIRouter()

SESSION_DAYS = 7
COOKIE_NAME = "session_token"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    token: str
    user_id: UUID
    expires_at: datetime
    tenant_id: UUID | None = None


class LogoutResponse(BaseModel):
    ok: bool = True


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


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate with email/password; create session; return token + metadata."""
    email = body.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Constant-ish failure path: verify only when user exists; generic error always.
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

    raw_token, token_hash = generate_session_token()
    expires_at = datetime.now(UTC) + timedelta(days=SESSION_DAYS)
    ip, ua = _client_meta(request)

    session = UserSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_revoked=False,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(session)
    await db.commit()

    tenant_id = await _primary_tenant_id(db, user.id)

    # HttpOnly cookie for cookie-path clients; raw token still returned for Admin Web.
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=False,  # local/dev; production should set Secure via reverse proxy TLS
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )

    return LoginResponse(
        token=raw_token,
        user_id=user.id,
        expires_at=expires_at,
        tenant_id=tenant_id,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    token: str = Depends(get_current_session_token),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LogoutResponse:
    """Revoke the current session (Bearer or cookie)."""
    import hashlib

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
