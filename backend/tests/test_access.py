from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.api.deps import current_tenant_id_var
from app.db.base import Base
from app.models.access import (
    AccessAttempt,
    AccessStatus,
    Checkin,
    Device,
    DeviceStatus,
    KeyStatus,
    OfflineSnapshot,
    SigningKey,
)
from app.models.location import Location
from app.models.member import Member


@pytest.fixture
async def access_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(Session, "after_begin")
    def mock_set_tenant_id(session, transaction, connection):
        pass

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def access_session_maker(access_engine):
    return async_sessionmaker(
        access_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest.mark.asyncio
async def test_signing_key_tenant_isolation(access_session_maker):
    tenant_id = uuid4()
    token = current_tenant_id_var.set(tenant_id)

    async with access_session_maker() as session:
        # Create ACTIVE key
        key1 = SigningKey(
            tenant_id=tenant_id,
            kid="qr-2026-08-a",
            status=KeyStatus.ACTIVE,
            key_material="secret_abc",
        )
        session.add(key1)

        # Create VERIFY_ONLY key
        key2 = SigningKey(
            tenant_id=tenant_id,
            kid="qr-2026-07",
            status=KeyStatus.VERIFY_ONLY,
            key_material="secret_xyz",
        )
        session.add(key2)

        await session.commit()

        result = await session.execute(
            select(SigningKey).filter_by(tenant_id=tenant_id)
        )
        keys_db = result.scalars().all()
        assert len(keys_db) == 2

        active_key = next((k for k in keys_db if k.status == KeyStatus.ACTIVE), None)
        assert active_key is not None
        assert active_key.kid == "qr-2026-08-a"

    current_tenant_id_var.reset(token)


@pytest.mark.asyncio
async def test_device_and_checkin_isolation(access_session_maker):
    tenant_id = uuid4()
    token = current_tenant_id_var.set(tenant_id)

    async with access_session_maker() as session:
        # Need a location and member
        loc = Location(tenant_id=tenant_id, name="Access Branch", timezone="UTC")
        session.add(loc)
        await session.commit()

        member = Member(
            tenant_id=tenant_id,
            member_number="A-001",
            first_name="Access",
            last_name="User",
        )
        session.add(member)
        await session.commit()

        # Create device
        device = Device(
            tenant_id=tenant_id,
            name="Main Gate QR",
            location_id=loc.id,
            capabilities=["QR_SCAN", "OFFLINE_CACHE"],
            status=DeviceStatus.ONLINE,
        )
        session.add(device)
        await session.commit()

        # Create offline snapshot
        snapshot = OfflineSnapshot(
            tenant_id=tenant_id,
            device_id=device.id,
            snapshot_type="member_allowlist",
            payload={"members": [str(member.id)]},
            version=1,
        )
        session.add(snapshot)

        # Access attempt
        attempt = AccessAttempt(
            tenant_id=tenant_id,
            member_id=member.id,
            device_id=device.id,
            status=AccessStatus.GRANTED,
            timestamp=datetime.now(UTC),
        )
        session.add(attempt)

        # Checkin
        checkin = Checkin(
            tenant_id=tenant_id,
            member_id=member.id,
            location_id=loc.id,
            device_id=device.id,
            checkin_time=datetime.now(UTC),
        )
        session.add(checkin)
        await session.commit()

        # Assertions
        devices_db = (
            (await session.execute(select(Device).filter_by(tenant_id=tenant_id)))
            .scalars()
            .all()
        )
        assert len(devices_db) == 1
        assert devices_db[0].status == DeviceStatus.ONLINE
        assert "QR_SCAN" in devices_db[0].capabilities

        attempts_db = (
            (
                await session.execute(
                    select(AccessAttempt).filter_by(tenant_id=tenant_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(attempts_db) == 1
        assert attempts_db[0].status == AccessStatus.GRANTED

        checkins_db = (
            (await session.execute(select(Checkin).filter_by(tenant_id=tenant_id)))
            .scalars()
            .all()
        )
        assert len(checkins_db) == 1
        assert checkins_db[0].member_id == member.id

        snapshots_db = (
            (
                await session.execute(
                    select(OfflineSnapshot).filter_by(tenant_id=tenant_id)
                )
            )
            .scalars()
            .all()
        )
        assert len(snapshots_db) == 1
        assert snapshots_db[0].version == 1
        assert str(member.id) in snapshots_db[0].payload["members"]

    current_tenant_id_var.reset(token)
