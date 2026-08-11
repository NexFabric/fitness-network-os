import secrets

import pyotp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import (
    decrypt_string,
    encrypt_string,
    get_password_hash,
)
from app.models.audit import AuditEvent
from app.models.user import User, UserMfaMethod

router = APIRouter()

class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    recovery_codes: list[str]

class MfaVerifyRequest(BaseModel):
    code: str

class MfaVerifyResponse(BaseModel):
    ok: bool

@router.post("/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new TOTP secret for the user, return URI and recovery codes."""
    # Check if active MFA exists
    result = await db.execute(select(UserMfaMethod).where(UserMfaMethod.user_id == current_user.id, UserMfaMethod.is_active == True))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="MFA is already active")
    
    # Clean up any inactive ones
    await db.execute(UserMfaMethod.__table__.delete().where(UserMfaMethod.user_id == current_user.id))

    totp_secret = pyotp.random_base32()
    provisioning_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(name=current_user.email, issuer_name="GymClubNex")
    
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

    return MfaSetupResponse(
        secret=totp_secret,
        provisioning_uri=provisioning_uri,
        recovery_codes=raw_recovery_codes,
    )

@router.post("/verify", response_model=MfaVerifyResponse)
async def verify_mfa_setup(
    body: MfaVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify the TOTP code to activate MFA."""
    result = await db.execute(select(UserMfaMethod).where(UserMfaMethod.user_id == current_user.id, UserMfaMethod.is_active == False))
    mfa_method = result.scalars().first()
    
    if not mfa_method or not mfa_method.encrypted_secret:
        raise HTTPException(status_code=400, detail="No pending MFA setup")
    
    totp_secret = decrypt_string(mfa_method.encrypted_secret)
    totp = pyotp.TOTP(totp_secret)
    if not totp.verify(body.code):
        raise HTTPException(status_code=400, detail="Invalid code")
    
    mfa_method.is_active = True
    
    db.add(AuditEvent(
        user_id=current_user.id,
        action="mfa_enabled",
        resource_type="user",
        resource_id=current_user.id,
    ))
    
    await db.commit()
    return MfaVerifyResponse(ok=True)
