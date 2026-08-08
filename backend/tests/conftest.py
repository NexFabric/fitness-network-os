import pytest
import pytest_asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.db.base import Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/gym_test")
TEST_RUNTIME_DATABASE_URL = os.getenv("TEST_RUNTIME_DATABASE_URL", "postgresql+asyncpg://app_user:app_password@localhost:5433/gym_test")

@pytest_asyncio.fixture(scope="function")
async def pg_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP OWNED BY app_user CASCADE;"))
            await conn.execute(text("DROP ROLE IF EXISTS app_user;"))
    except Exception:
        pass
    
    async with engine.begin() as conn:
        await conn.execute(text("CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password' NOSUPERUSER NOBYPASSRLS;"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO app_user;"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;"))
        await conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;"))
        await conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;"))
        
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP OWNED BY app_user CASCADE;"))
        await conn.execute(text("DROP ROLE IF EXISTS app_user;"))
        
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def pg_session_maker(pg_engine):
    runtime_engine = create_async_engine(TEST_RUNTIME_DATABASE_URL, echo=False)
    yield async_sessionmaker(runtime_engine, class_=AsyncSession, expire_on_commit=False)
    await runtime_engine.dispose()
