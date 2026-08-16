"""Service-level booking catalog branches (not HTTP)."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.tenant import Tenant
from app.schemas.booking import ClassTypeCreate, ClassTypeUpdate
from app.services.booking import BookingNotFound, ClassBookingService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Bk Org", domain=f"bk-{uuid4().hex[:8]}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid4(),
        name="Bk Tenant",
        organization_id=org.id,
        location_code=f"BK-{uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_class_type_crud_and_not_found(db_session, tenant):
    created = await ClassBookingService.create_class_type(
        db_session,
        tenant.id,
        ClassTypeCreate(name="HIIT", default_capacity=8),
    )
    await db_session.commit()
    listed = await ClassBookingService.list_class_types(db_session, tenant.id)
    assert [row.id for row in listed] == [created.id]

    fetched = await ClassBookingService.get_class_type(
        db_session, tenant.id, created.id
    )
    assert fetched.name == "HIIT"

    updated = await ClassBookingService.update_class_type(
        db_session,
        tenant.id,
        created.id,
        ClassTypeUpdate(name="HIIT Plus", is_active=False),
    )
    await db_session.commit()
    assert updated.name == "HIIT Plus"
    active_only = await ClassBookingService.list_class_types(db_session, tenant.id)
    assert active_only == []
    all_rows = await ClassBookingService.list_class_types(
        db_session, tenant.id, active_only=False
    )
    assert len(all_rows) == 1

    with pytest.raises(BookingNotFound):
        await ClassBookingService.get_class_type(db_session, tenant.id, uuid4())
