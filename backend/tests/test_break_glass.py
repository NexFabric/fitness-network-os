import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import AuditEvent
from app.models.break_glass import BreakGlassStatus
from app.models.organization import Organization
from app.models.user import User
from app.services.break_glass import BreakGlassService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def organization(db_session: AsyncSession) -> Organization:
    org = Organization(name="BreakGlass Org", domain=f"org-{uuid.uuid4()}.com")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"user-{uuid.uuid4()}@test.com",
        hashed_password="hash",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_break_glass_service_creation(
    db_session: AsyncSession, user: User, organization: Organization
):
    service = BreakGlassService(db_session)
    tenant_id = uuid.uuid4()

    # Test valid creation
    session = await service.create_session(
        actor_id=user.id,
        target_tenant_id=tenant_id,
        reason="Prod incident",
        ticket_reference="INC-1234",
        duration_minutes=30,
    )

    assert session.status == BreakGlassStatus.ACTIVE.value
    assert session.actor_id == user.id
    assert session.reason == "Prod incident"

    # Test duration capping (min 5)
    session_min = await service.create_session(
        actor_id=user.id,
        target_tenant_id=tenant_id,
        reason="Prod incident 2",
        ticket_reference="INC-1235",
        duration_minutes=1,
    )
    diff_min = session_min.expires_at - session_min.granted_at
    assert 4 < diff_min.total_seconds() / 60 <= 5

    # Test duration capping (max 60)
    session_max = await service.create_session(
        actor_id=user.id,
        target_tenant_id=tenant_id,
        reason="Prod incident 3",
        ticket_reference="INC-1236",
        duration_minutes=120,
    )
    diff_max = session_max.expires_at - session_max.granted_at
    assert 59 < diff_max.total_seconds() / 60 <= 60

    # Test audit event creation
    result = await db_session.execute(
        select(AuditEvent).where(
            AuditEvent.action == "break_glass.session_created",
            AuditEvent.resource_id == tenant_id,
        )
    )
    audits = result.scalars().all()
    assert len(audits) >= 3


@pytest.mark.asyncio
async def test_break_glass_auto_expiry(db_session, user):
    service = BreakGlassService(db_session)
    tenant_id = uuid.uuid4()

    session = await service.create_session(
        actor_id=user.id,
        target_tenant_id=tenant_id,
        reason="Test",
        ticket_reference="INC-1",
    )

    # Manually expire it
    session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.commit()

    # Check should auto-transition
    active = await service.check_active_session(user.id, tenant_id)
    assert active is None

    await db_session.refresh(session)
    assert session.status == BreakGlassStatus.EXPIRED.value


@pytest.mark.asyncio
async def test_break_glass_revocation(db_session, user):
    service = BreakGlassService(db_session)
    tenant_id = uuid.uuid4()

    session = await service.create_session(
        actor_id=user.id,
        target_tenant_id=tenant_id,
        reason="Test",
        ticket_reference="INC-2",
    )

    revoked = await service.revoke_session(session.id, user.id)
    assert revoked.status == BreakGlassStatus.REVOKED.value
    assert revoked.revoked_at is not None

    # Audit for revocation
    result = await db_session.execute(
        select(AuditEvent).where(
            AuditEvent.action == "break_glass.session_revoked",
            AuditEvent.resource_id == session.id,
        )
    )
    audit = result.scalars().first()
    assert audit is not None
