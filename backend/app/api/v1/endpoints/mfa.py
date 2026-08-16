import hashlib
import logging
import secrets
from datetime import UTC, datetime

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_session_token,
    get_current_user,
    get_db,
    get_mfa_enrollment_user,
)
from app.api.v1.endpoints.auth import resolve_auth_level, session_lifetime
from app.core.security import (
    decrypt_string,
    encrypt_string,
    generate_session_token,
    get_password_hash,
)
from app.models.audit import AuditEvent
from app.models.user import User, UserMfaMethod, UserSession

router = APIRouter()
logger = logging.getLogger(__name__)
COOKIE_NAME = "session_token"


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    recovery_codes: list[str]


class MfaVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class MfaVerifyResponse(BaseModel):
    success: bool
    password_change_required: bool = False


@router.post("/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    response: Response,
    current_user: User = Depends(get_mfa_enrollment_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new TOTP secret for the user, return URI and recovery codes."""
    # Check if active MFA exists
    result = await db.execute(
        select(UserMfaMethod).where(
            UserMfaMethod.user_id == current_user.id, UserMfaMethod.is_active == True
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="MFA is already active")

    # Clean up any inactive ones
    await db.execute(
        delete(UserMfaMethod).where(UserMfaMethod.user_id == current_user.id)
    )

    totp_secret = pyotp.random_base32()
    provisioning_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
        name=current_user.email, issuer_name="GymClubNex"
    )

    raw_recovery_codes = [secrets.token_hex(8) for _ in range(8)]
    hashed_codes = [get_password_hash(c) for c in raw_recovery_codes]

    new_mfa = UserMfaMethod(
        user_id=current_user.id,
        encrypted_secret=encrypt_string(totp_secret),
        hashed_recovery_codes=hashed_codes,
        provider_id="totp",
        is_active=False,
    )
    db.add(new_mfa)
    await db.commit()

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return MfaSetupResponse(
        secret=totp_secret,
        provisioning_uri=provisioning_uri,
        recovery_codes=raw_recovery_codes,
    )


@router.post("/verify", response_model=MfaVerifyResponse)
async def verify_mfa_setup(
    body: MfaVerifyRequest,
    response: Response,
    current_user: User = Depends(get_mfa_enrollment_user),
    token: str = Depends(get_current_session_token),
    db: AsyncSession = Depends(get_db),
):
    """Verify the TOTP code to activate MFA."""
    result = await db.execute(
        select(UserMfaMethod).where(
            UserMfaMethod.user_id == current_user.id, UserMfaMethod.is_active == False
        )
    )
    mfa_method = result.scalars().first()

    if not mfa_method or not mfa_method.encrypted_secret:
        raise HTTPException(status_code=400, detail="No pending MFA setup")

    totp_secret = decrypt_string(mfa_method.encrypted_secret)
    totp = pyotp.TOTP(totp_secret)
    if not totp.verify(body.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid code")

    mfa_method.is_active = True

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = (
        await db.execute(
            select(UserSession).where(
                UserSession.token_hash == token_hash,
                UserSession.user_id == current_user.id,
                UserSession.is_revoked.is_(False),
            )
        )
    ).scalar_one()
    session.is_revoked = True
    raw_session_token, new_token_hash = generate_session_token()
    # Enrollment is not automatically the last gate. An account provisioned with
    # a one-time password still owes a rotation, so ask for the level rather than
    # assuming "full" — otherwise finishing MFA would skip that requirement.
    next_level = resolve_auth_level(
        current_user, has_active_mfa=True, privileged_mfa=True
    )
    expires_at = datetime.now(UTC) + session_lifetime(next_level)
    db.add(
        UserSession(
            user_id=current_user.id,
            token_hash=new_token_hash,
            expires_at=expires_at,
            is_revoked=False,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            auth_level=next_level,
        )
    )

    tenant_id = next(
        (
            user_role.tenant_id
            for user_role in current_user.user_roles
            if user_role.tenant_id is not None
        ),
        None,
    )
    if tenant_id is not None:
        await db.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        db.add(
            AuditEvent(
                tenant_id=tenant_id,
                user_id=current_user.id,
                action="mfa_enabled",
                resource_type="user",
                resource_id=current_user.id,
            )
        )
    else:
        # The existing audit table is intentionally tenant-owned. Platform and
        # federation principals have no tenant row to attach; keep an explicit
        # structured security log until a global audit domain is introduced.
        logger.info(
            "auth.mfa_enabled scope=global user_id=%s",
            current_user.id,
        )

    await db.commit()

    from app.core.config import settings

    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_session_token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=int(session_lifetime(next_level).total_seconds()),
        path="/",
    )
    return MfaVerifyResponse(
        success=True, password_change_required=next_level == "password_reset"
    )


class StepUpRequest(BaseModel):
    code: str = Field(min_length=6, max_length=32)


class StepUpResponse(BaseModel):
    ok: bool = True


@router.post("/step-up", response_model=StepUpResponse)
async def step_up_mfa(
    body: StepUpRequest,
    token: str = Depends(get_current_session_token),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-verify TOTP and stamp the current full session for sensitive writes."""
    import hashlib
    from datetime import datetime

    from app.core.security import decrypt_string, verify_password

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
    if mfa_row is None or not mfa_row.encrypted_secret:
        raise HTTPException(status_code=400, detail="mfa_not_enrolled")

    code = body.code.strip()
    valid = False
    totp = pyotp.TOTP(decrypt_string(mfa_row.encrypted_secret))
    if totp.verify(code, valid_window=1):
        valid = True
    if not valid and mfa_row.hashed_recovery_codes:
        for idx, hcode in enumerate(mfa_row.hashed_recovery_codes):
            if verify_password(code, hcode):
                valid = True
                mfa_row.hashed_recovery_codes.pop(idx)
                mfa_row.hashed_recovery_codes = list(mfa_row.hashed_recovery_codes)
                break
    if not valid:
        raise HTTPException(status_code=401, detail="mfa_invalid")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = (
        await db.execute(
            select(UserSession).where(
                UserSession.token_hash == token_hash,
                UserSession.user_id == current_user.id,
                UserSession.is_revoked.is_(False),
            )
        )
    ).scalar_one()
    session.last_step_up_at = datetime.now(UTC)
    await db.commit()
    return StepUpResponse()
