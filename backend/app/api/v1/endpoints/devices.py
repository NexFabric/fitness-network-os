import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_device,
    get_current_user,
    get_db,
    get_tenant_id,
    require_recent_step_up,
)
from app.api.v1.endpoints.access import ValidateQrRequest, ValidateQrResponse
from app.core.authorization import AuthorizationService
from app.core.device_auth import MAX_CLOCK_SKEW_SECONDS, new_device_signing_material
from app.core.security import generate_session_token
from app.models.access import Device, DeviceSession, DeviceStatus
from app.models.audit import AuditEvent
from app.models.location import Location
from app.models.user import User
from app.services.access import AccessService

router = APIRouter()

DEVICE_SESSION_DAYS = 30
DEVICE_COOKIE_NAME = "device_session"


class ProvisionDeviceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location_id: UUID


class ProvisionDeviceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    location_id: UUID
    api_key: str


class DeviceAuthRequest(BaseModel):
    device_id: UUID
    tenant_id: UUID
    api_key: str


class DeviceAuthResponse(BaseModel):
    device_id: UUID
    tenant_id: UUID
    location_id: UUID
    expires_at: datetime
    session_id: UUID
    # Returned exactly once, here. The device stores it locally and signs every
    # subsequent request with it; it is never accepted back over the wire.
    signing_secret: str
    signature_algorithm: str = "HMAC-SHA256"
    max_clock_skew_seconds: int = MAX_CLOCK_SKEW_SECONDS


class RevokeDeviceRequest(BaseModel):
    device_id: UUID


class DeviceResponse(BaseModel):
    id: UUID
    name: str
    location_id: UUID
    status: str
    is_active: bool
    last_heartbeat_at: datetime | None

    model_config = {"from_attributes": True}


def _hash_api_key(api_key: str) -> str:
    """Hash the API key using SHA-256 for storage.

    Deliberately a fast hash, not Argon2. The key is never chosen by a human:
    ``provision_device`` mints it as ``secrets.token_urlsafe(32)`` — 256 bits of
    CSPRNG entropy — so there is no guessable keyspace for a slow KDF to defend.
    A memory-hard hash here would only add latency to every scanner auth. Human
    passwords take the opposite path (``app.core.security.get_password_hash``,
    Argon2id). Static analysis flags this on the ``api_key`` name alone.
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


@router.post("/provision", response_model=ProvisionDeviceResponse)
async def provision_device(
    body: ProvisionDeviceRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(require_recent_step_up),
    db: AsyncSession = Depends(get_db),
):
    """Staff only: Provision a new physical scanner device."""
    AuthorizationService.require_tenant(current_user, "devices:manage", tenant_id)

    location = await db.get(Location, body.location_id)
    if location is None or location.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Lokasyon bulunamadı.")

    raw_api_key = secrets.token_urlsafe(32)
    api_key_hash = _hash_api_key(raw_api_key)

    device = Device(
        tenant_id=tenant_id,
        name=body.name,
        location_id=body.location_id,
        status=DeviceStatus.OFFLINE,
        api_key_hash=api_key_hash,
        is_active=True,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)

    db.add(
        AuditEvent(
            tenant_id=tenant_id,
            user_id=current_user.id,
            action="device_provisioned",
            resource_type="device",
            resource_id=device.id,
            new_state={"name": device.name, "location_id": str(device.location_id)},
        )
    )
    await db.commit()

    return ProvisionDeviceResponse(
        id=device.id,
        tenant_id=device.tenant_id,
        name=device.name,
        location_id=device.location_id,
        api_key=raw_api_key,
    )


@router.post("/auth", response_model=DeviceAuthResponse)
async def auth_device(
    body: DeviceAuthRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Public: Device authenticates with ID, Tenant ID and API key to receive a session."""
    from sqlalchemy import text

    await db.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(body.tenant_id)},
    )

    result = await db.execute(select(Device).where(Device.id == body.device_id))
    device = result.scalar_one_or_none()

    if not device or not device.is_active or not device.api_key_hash:
        raise HTTPException(status_code=401, detail="Invalid device credentials")

    expected_hash = _hash_api_key(body.api_key)
    if not secrets.compare_digest(expected_hash, device.api_key_hash):
        raise HTTPException(status_code=401, detail="Invalid device credentials")

    device.status = DeviceStatus.ONLINE
    device.last_heartbeat_at = datetime.now(UTC)

    raw_token, token_hash = generate_session_token()
    expires_at = datetime.now(UTC) + timedelta(days=DEVICE_SESSION_DAYS)

    ip = request.client.host if request.client else None

    key_material, raw_signing_secret = new_device_signing_material()

    session = DeviceSession(
        tenant_id=device.tenant_id,
        device_id=device.id,
        token_hash=token_hash,
        ip_address=ip,
        expires_at=expires_at,
        is_revoked=False,
        signing_key_material=key_material,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    from app.core.config import settings

    response.set_cookie(
        key=DEVICE_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=DEVICE_SESSION_DAYS * 24 * 3600,
        path="/",
    )

    return DeviceAuthResponse(
        device_id=device.id,
        tenant_id=device.tenant_id,
        location_id=device.location_id,
        expires_at=expires_at,
        session_id=session.id,
        signing_secret=raw_signing_secret,
    )


@router.post("/revoke")
async def revoke_device(
    body: RevokeDeviceRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Staff only: Revoke a device and all its active sessions immediately."""
    AuthorizationService.require_tenant(current_user, "devices:manage", tenant_id)

    result = await db.execute(
        select(Device).where(Device.id == body.device_id, Device.tenant_id == tenant_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.is_active = False
    device.api_key_hash = None  # prevent future usage of the same key entirely
    old_status = device.status
    device.status = DeviceStatus.OFFLINE

    # Revoke sessions
    from sqlalchemy import update

    await db.execute(
        update(DeviceSession)
        .where(DeviceSession.device_id == device.id)
        .values(is_revoked=True)
    )

    db.add(
        AuditEvent(
            tenant_id=tenant_id,
            user_id=current_user.id,
            action="device_revoked",
            resource_type="device",
            resource_id=device.id,
            old_state={"status": old_status, "is_active": True},
            new_state={"status": DeviceStatus.OFFLINE, "is_active": False},
        )
    )

    await db.commit()
    return {"ok": True}


@router.get("/", response_model=list[DeviceResponse])
async def list_devices(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Staff only: List devices."""
    AuthorizationService.require_tenant(current_user, "devices:manage", tenant_id)

    result = await db.execute(select(Device).where(Device.tenant_id == tenant_id))
    return result.scalars().all()


@router.post("/qr/validate", response_model=ValidateQrResponse)
async def device_validate_qr(
    body: ValidateQrRequest,
    current_device: Device = Depends(get_current_device),
    db: AsyncSession = Depends(get_db),
):
    """Device only: Validate a QR code scanned by a physical device."""
    svc = AccessService(db)

    # Overwrite the request device_id and location_id with the trusted device's real ones
    result = await svc.validate_qr(
        current_device.tenant_id,
        body.token,
        device_id=current_device.id,
        location_id=current_device.location_id,
        action=body.action,
        consume=body.consume,
        quantity=int(body.quantity),
    )
    await db.commit()

    status_code = status.HTTP_200_OK if result.granted else status.HTTP_403_FORBIDDEN
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
