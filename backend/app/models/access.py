import enum
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
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


class AccessMethod(str, enum.Enum):
    QR_SCAN = "QR_SCAN"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"


class SigningKey(TenantMixin, Base):
    """Tenant QR/access signing key metadata.

    ``key_material`` stores a secret-manager *reference* (or ``local:hmac:…``
    for pre-production). Raw keys must never be logged.
    """

    __tablename__ = "signing_keys"

    kid: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[KeyStatus] = mapped_column(
        Enum(KeyStatus, name="key_status_enum", create_type=False),
        nullable=False,
        default=KeyStatus.ACTIVE,
    )
    algorithm: Mapped[str] = mapped_column(String(32), nullable=False, default="HMAC_SHA256")
    key_material: Mapped[str] = mapped_column(String(512), nullable=False)

    _model_table_args = (
        UniqueConstraint("tenant_id", "kid", name="uq_signing_keys_tenant_kid"),
    )


class Device(TenantMixin, Base):
    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(String, nullable=False)
    location_id: Mapped[UUID] = mapped_column(nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list
    )
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, name="device_status_enum", create_type=False),
        nullable=False,
        default=DeviceStatus.OFFLINE,
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "location_id"], ["locations.tenant_id", "locations.id"]
        ),
    )

    location = relationship("Location")


class AccessAttempt(TenantMixin, Base):
    __tablename__ = "access_attempts"

    member_id: Mapped[UUID | None] = mapped_column(nullable=True)
    device_id: Mapped[UUID | None] = mapped_column(nullable=True)
    status: Mapped[AccessStatus] = mapped_column(
        Enum(AccessStatus, name="access_status_enum", create_type=False),
        nullable=False,
    )
    denial_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    jti: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    method: Mapped[str | None] = mapped_column(String(32), nullable=True, default="QR_SCAN")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "device_id"], ["devices.tenant_id", "devices.id"]
        ),
    )

    member = relationship("Member", overlaps="device")
    device = relationship("Device", overlaps="member")


class Checkin(TenantMixin, Base):
    __tablename__ = "checkins"

    member_id: Mapped[UUID] = mapped_column(nullable=False)
    location_id: Mapped[UUID] = mapped_column(nullable=False)
    device_id: Mapped[UUID | None] = mapped_column(nullable=True)
    checkin_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    checkout_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "location_id"], ["locations.tenant_id", "locations.id"]
        ),
        ForeignKeyConstraint(
            ["tenant_id", "device_id"], ["devices.tenant_id", "devices.id"]
        ),
    )

    member = relationship("Member", overlaps="location,device")
    location = relationship("Location", overlaps="member,device")
    device = relationship("Device", overlaps="member,location")


class OfflineSnapshot(TenantMixin, Base):
    __tablename__ = "offline_snapshots"

    device_id: Mapped[UUID] = mapped_column(nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    version: Mapped[int] = mapped_column(nullable=False, default=1)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "device_id"], ["devices.tenant_id", "devices.id"]
        ),
    )

    device = relationship("Device")


class QrJtiReplay(TenantMixin, Base):
    """Consumed QR jti values for replay protection (tenant-scoped)."""

    __tablename__ = "qr_jti_replays"

    jti: Mapped[str] = mapped_column(String(64), nullable=False)
    member_id: Mapped[UUID | None] = mapped_column(nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    _model_table_args = (
        UniqueConstraint("tenant_id", "jti", name="uq_qr_jti_replays_tenant_jti"),
        ForeignKeyConstraint(
            ["tenant_id", "member_id"], ["members.tenant_id", "members.id"]
        ),
    )
