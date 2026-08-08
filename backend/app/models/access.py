import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin


class KeyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    VERIFY_ONLY = "VERIFY_ONLY"
    REVOKED = "REVOKED"

class DeviceStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    CLOCK_DRIFT = "CLOCK_DRIFT"
    SYNC_PENDING = "SYNC_PENDING"
    CERTIFICATE_EXPIRING = "CERTIFICATE_EXPIRING"

class AccessStatus(str, enum.Enum):
    GRANTED = "GRANTED"
    DENIED = "DENIED"

class SigningKey(TenantMixin, Base):
    __tablename__ = "signing_keys"

    kid: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    status: Mapped[KeyStatus] = mapped_column(Enum(KeyStatus, name="key_status_enum", create_type=False), nullable=False, default=KeyStatus.ACTIVE)
    key_material: Mapped[str] = mapped_column(String(200), nullable=False) # E.g., AWS KMS ARN or Vault path
    
class Device(TenantMixin, Base):
    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(String, nullable=False)
    location_id: Mapped[UUID] = mapped_column(nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    status: Mapped[DeviceStatus] = mapped_column(Enum(DeviceStatus, name="device_status_enum", create_type=False), nullable=False, default=DeviceStatus.OFFLINE)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "location_id"], ["locations.tenant_id", "locations.id"]),
    )

    location = relationship("Location")
    
class AccessAttempt(TenantMixin, Base):
    __tablename__ = "access_attempts"

    member_id: Mapped[UUID | None] = mapped_column(nullable=True)
    device_id: Mapped[UUID | None] = mapped_column(nullable=True)
    status: Mapped[AccessStatus] = mapped_column(Enum(AccessStatus, name="access_status_enum", create_type=False), nullable=False)
    denial_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
        ForeignKeyConstraint(["tenant_id", "device_id"], ["devices.tenant_id", "devices.id"]),
    )

    member = relationship("Member")
    device = relationship("Device")

class Checkin(TenantMixin, Base):
    __tablename__ = "checkins"

    member_id: Mapped[UUID] = mapped_column(nullable=False)
    location_id: Mapped[UUID] = mapped_column(nullable=False)
    device_id: Mapped[UUID | None] = mapped_column(nullable=True)
    checkin_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    checkout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "member_id"], ["members.tenant_id", "members.id"]),
        ForeignKeyConstraint(["tenant_id", "location_id"], ["locations.tenant_id", "locations.id"]),
        ForeignKeyConstraint(["tenant_id", "device_id"], ["devices.tenant_id", "devices.id"]),
    )

    member = relationship("Member")
    location = relationship("Location")
    device = relationship("Device")

class OfflineSnapshot(TenantMixin, Base):
    __tablename__ = "offline_snapshots"

    device_id: Mapped[UUID] = mapped_column(nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String, nullable=False) # e.g., 'member_allowlist'
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    
    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "device_id"], ["devices.tenant_id", "devices.id"]),
    )

    device = relationship("Device")
