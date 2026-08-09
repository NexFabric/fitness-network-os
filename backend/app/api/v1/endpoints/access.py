from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, StrictInt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService
from app.models.user import User
from app.services.access import AccessService
from app.services.member import MemberService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    """Tenant-scoped staff permission check (non-:self)."""
    AuthorizationService.require_tenant(user, permission, tenant_id)


class IssueQrRequest(BaseModel):
    """Staff-only: issue QR for an arbitrary member_id."""

    member_id: UUID
    ttl_seconds: StrictInt = Field(default=60, ge=15, le=600)


class IssueSelfQrRequest(BaseModel):
    """Member self-issue: member_id is never accepted — resolved via user binding."""

    ttl_seconds: StrictInt = Field(default=60, ge=15, le=600)


class IssueQrResponse(BaseModel):
    token: str
    kid: str
    jti: str
    credential_id: str
    exp: datetime
    iat: datetime
    member_id: UUID | None = None


class ValidateQrRequest(BaseModel):
    token: str
    device_id: UUID | None = None
    location_id: UUID | None = None
    action: str = "GYM_ENTRY"
    consume: bool = False
    quantity: StrictInt = Field(default=1, ge=1)


class ValidateQrResponse(BaseModel):
    granted: bool
    reason: str | None = None
    member_id: UUID | None = None
    jti: str | None = None
    attempt_id: UUID | None = None
    checkin_id: UUID | None = None
    remaining: int | None = None


class SigningKeyResponse(BaseModel):
    id: UUID
    kid: str
    status: str
    algorithm: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RotateKeyResponse(BaseModel):
    kid: str
    status: str
    algorithm: str


@router.post("/qr/issue", response_model=IssueQrResponse)
async def issue_qr(
    body: IssueQrRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Staff path: requires access:issue; body.member_id is mandatory."""
    _require(current_user, tenant_id, "access:issue")
    svc = AccessService(db)
    try:
        result = await svc.issue_qr_token(
            tenant_id,
            body.member_id,
            ttl_seconds=int(body.ttl_seconds),
        )
        await db.commit()
        return IssueQrResponse(
            token=result.token,
            kid=result.kid,
            jti=result.jti,
            credential_id=result.credential_id,
            exp=result.exp,
            iat=result.iat,
            member_id=body.member_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/qr/issue-self", response_model=IssueQrResponse)
async def issue_qr_self(
    body: IssueSelfQrRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Member self-QR: requires access:issue:self; never accepts body.member_id.

    Resolves Member via members.user_id == current_user.id within tenant.
    Ownership proof: resource_owner_id=current_user.id (required for *:self).
    """
    AuthorizationService.require_self(
        current_user,
        "access:issue:self",
        tenant_id,
        resource_owner_id=current_user.id,
    )
    members = MemberService(db)
    member = await members.get_member_by_user_id(tenant_id, current_user.id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="member_not_bound",
        )
    svc = AccessService(db)
    try:
        result = await svc.issue_qr_token(
            tenant_id,
            member.id,
            ttl_seconds=int(body.ttl_seconds),
        )
        await db.commit()
        return IssueQrResponse(
            token=result.token,
            kid=result.kid,
            jti=result.jti,
            credential_id=result.credential_id,
            exp=result.exp,
            iat=result.iat,
            member_id=member.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/qr/validate", response_model=ValidateQrResponse)
async def validate_qr(
    body: ValidateQrRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "access:validate")
    svc = AccessService(db)
    result = await svc.validate_qr(
        tenant_id,
        body.token,
        device_id=body.device_id,
        location_id=body.location_id,
        action=body.action,
        consume=body.consume,
        quantity=int(body.quantity),
    )
    await db.commit()
    status_code = status.HTTP_200_OK if result.granted else status.HTTP_403_FORBIDDEN
    # Return body with appropriate status: use Response would lose model —
    # keep 200 with granted flag for machine clients; 403 when denied is clearer.
    if not result.granted and result.reason == "replay":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "granted": False,
                "reason": "replay",
                "jti": result.jti,
                "member_id": str(result.member_id) if result.member_id else None,
            },
        )
    if not result.granted:
        raise HTTPException(
            status_code=status_code,
            detail={
                "granted": False,
                "reason": result.reason,
                "jti": result.jti,
                "member_id": str(result.member_id) if result.member_id else None,
                "remaining": result.remaining,
            },
        )
    return ValidateQrResponse(
        granted=result.granted,
        reason=result.reason,
        member_id=result.member_id,
        jti=result.jti,
        attempt_id=result.attempt_id,
        checkin_id=result.checkin_id,
        remaining=result.remaining,
    )


@router.post("/keys/rotate", response_model=RotateKeyResponse)
async def rotate_key(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "access:keys")
    svc = AccessService(db)
    key = await svc.rotate_signing_key(tenant_id)
    await db.commit()
    return RotateKeyResponse(
        kid=key.kid, status=key.status.value if hasattr(key.status, "value") else str(key.status), algorithm=key.algorithm
    )


@router.get("/keys", response_model=list[SigningKeyResponse])
async def list_keys(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "access:keys")
    svc = AccessService(db)
    keys = await svc.list_keys(tenant_id)
    return [
        SigningKeyResponse(
            id=k.id,
            kid=k.kid,
            status=k.status.value if hasattr(k.status, "value") else str(k.status),
            algorithm=k.algorithm,
            created_at=k.created_at,
        )
        for k in keys
    ]
