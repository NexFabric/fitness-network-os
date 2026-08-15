import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.retention import DataRetentionPolicy, DeletionMethod
from app.models.tenant import Tenant


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    org = Organization(name="Retention Org", domain=f"ret-{uuid.uuid4()}.com")
    db_session.add(org)
    await db_session.flush()
    t = Tenant(
        id=uuid.uuid4(),
        name="Retention Tenant",
        organization_id=org.id,
        location_code=f"LOC-{uuid.uuid4().hex[:6]}",
    )
    db_session.add(t)
    await db_session.commit()
    return t


@pytest.mark.asyncio
async def test_data_retention_policy_creation(db_session: AsyncSession, tenant: Tenant):
    policy = DataRetentionPolicy(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        data_category="user_activity_logs",
        description="Activity logs for user accounts",
        retention_days=90,
        deletion_method=DeletionMethod.DELETE.value,
        legal_basis="Consent",
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)

    assert policy.data_category == "user_activity_logs"
    assert policy.retention_days == 90
    assert policy.deletion_method == "DELETE"
    assert policy.requires_legal_review is True


@pytest.mark.asyncio
async def test_deletion_method_enum(db_session, tenant):
    # Test valid enum value
    policy = DataRetentionPolicy(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        data_category="payment_history",
        description="Payment history records",
        retention_days=365,
        deletion_method=DeletionMethod.ARCHIVE.value,
    )
    db_session.add(policy)
    await db_session.commit()

    # Test invalid enum value
    invalid_policy = DataRetentionPolicy(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        data_category="invalid_enum",
        description="Invalid",
        retention_days=10,
        deletion_method="DESTROY",
    )
    db_session.add(invalid_policy)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_retention_days_constraint(db_session, tenant):
    # Test NULL is valid
    null_policy = DataRetentionPolicy(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        data_category="audit_logs",
        description="Core audit logs",
        retention_days=None,
    )
    db_session.add(null_policy)
    await db_session.commit()

    # Test negative is invalid
    negative_policy = DataRetentionPolicy(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        data_category="temp_logs",
        description="Temporary logs",
        retention_days=-1,
    )
    db_session.add(negative_policy)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_unique_tenant_category(db_session, tenant):
    policy1 = DataRetentionPolicy(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        data_category="duplicate_category",
        description="First instance",
    )
    db_session.add(policy1)
    await db_session.commit()

    policy2 = DataRetentionPolicy(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        data_category="duplicate_category",
        description="Second instance should fail",
    )
    db_session.add(policy2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()
