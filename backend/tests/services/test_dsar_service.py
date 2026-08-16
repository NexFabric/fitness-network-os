"""DSAR service branches beyond the HTTP export/erasure specs."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.member import Member
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.services.dsar import DsarService, _assert_package_safe


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest.mark.asyncio
async def test_dsar_list_and_get(db_session: AsyncSession):
    org = Organization(name="Dsar Org", domain=f"ds-{uuid4().hex[:8]}.com")
    db_session.add(org)
    await db_session.flush()
    tenant = Tenant(
        id=uuid4(),
        name="Dsar T",
        organization_id=org.id,
        location_code=f"DS-{uuid4().hex[:6]}",
    )
    db_session.add(tenant)
    await db_session.flush()
    member = Member(
        id=uuid4(),
        tenant_id=tenant.id,
        member_number=f"M-{uuid4().hex[:6]}",
        first_name="Ada",
        last_name="Lovelace",
        email=f"ada-{uuid4().hex[:6]}@example.com",
    )
    db_session.add(member)
    await db_session.commit()

    svc = DsarService(db_session)
    row, created = await svc.request_export(
        tenant.id, member, requested_by_user_id=None
    )
    await db_session.commit()
    assert created is True
    again, created_again = await svc.request_export(
        tenant.id, member, requested_by_user_id=None
    )
    assert created_again is False
    assert again.id == row.id

    listed = await svc.list_for_member(tenant.id, member.id)
    assert [item.id for item in listed] == [row.id]
    tenant_list = await svc.list_for_tenant(tenant.id)
    assert [item.id for item in tenant_list] == [row.id]
    fetched = await svc.get(tenant.id, row.id)
    assert fetched is not None
    assert fetched.id == row.id
    assert await svc.get(tenant.id, uuid4()) is None


def test_dsar_package_rejects_secret_keys():
    with pytest.raises(ValueError, match="package_contains_secret:hashed_password"):
        _assert_package_safe({"profile": {"hashed_password": "x"}})
    _assert_package_safe({"email": "a@b.c", "invoices": [{"amount_minor": 100}]})
