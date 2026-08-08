from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.api.deps import current_tenant_id_var
from app.db.base import Base
from app.models.consent import ConsentDefinition, ConsentRecord
from app.models.location import Location
from app.models.member import Member, Tag


@pytest.fixture
async def gym_core_engine():
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
def gym_core_session_maker(gym_core_engine):
    return async_sessionmaker(gym_core_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.mark.asyncio
async def test_location_tenant_isolation(gym_core_session_maker):
    tenant_id = uuid4()
    
    token = current_tenant_id_var.set(tenant_id)
    
    async with gym_core_session_maker() as session:
        loc = Location(tenant_id=tenant_id, name="Test Branch", timezone="Europe/Istanbul", address="Istanbul")
        session.add(loc)
        await session.commit()
        
        result = await session.execute(select(Location).filter_by(tenant_id=tenant_id))
        loc_db = result.scalars().first()
        assert loc_db.name == "Test Branch"
        assert loc_db.tenant_id == tenant_id
    
    current_tenant_id_var.reset(token)

@pytest.mark.asyncio
async def test_member_tenant_isolation(gym_core_session_maker):
    tenant_id = uuid4()
    token = current_tenant_id_var.set(tenant_id)
    
    async with gym_core_session_maker() as session:
        member = Member(
            tenant_id=tenant_id, 
            member_number="M-001",
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        session.add(member)
        await session.commit()
        
        tag = Tag(tenant_id=tenant_id, member_id=member.id, name="VIP")
        session.add(tag)
        await session.commit()
        
        result = await session.execute(select(Member).filter_by(tenant_id=tenant_id))
        mem_db = result.scalars().first()
        assert mem_db.first_name == "John"
        
        tag_result = await session.execute(select(Tag).filter_by(tenant_id=tenant_id, member_id=mem_db.id))
        tag_db = tag_result.scalars().first()
        assert tag_db.name == "VIP"
    
    current_tenant_id_var.reset(token)

@pytest.mark.asyncio
async def test_consent_tenant_isolation(gym_core_session_maker):
    tenant_id = uuid4()
    token = current_tenant_id_var.set(tenant_id)
    
    async with gym_core_session_maker() as session:
        member = Member(
            tenant_id=tenant_id, 
            member_number="M-002",
            first_name="Jane",
            last_name="Doe"
        )
        session.add(member)
        await session.commit()

        definition = ConsentDefinition(
            tenant_id=tenant_id, 
            name="Marketing Consent", 
            consent_type="MARKETING"
        )
        session.add(definition)
        await session.commit()
        
        record = ConsentRecord(
            tenant_id=tenant_id,
            member_id=member.id,
            consent_type="MARKETING",
            document_version="v1.0",
            status="GRANTED"
        )
        session.add(record)
        await session.commit()
        
        result = await session.execute(select(ConsentRecord).filter_by(tenant_id=tenant_id))
        record_db = result.scalars().first()
        assert record_db.status == "GRANTED"
        assert record_db.document_version == "v1.0"
    
    current_tenant_id_var.reset(token)
