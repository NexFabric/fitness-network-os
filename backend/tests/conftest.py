import os
import subprocess
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/gym_test")
TEST_RUNTIME_DATABASE_URL = os.getenv("TEST_RUNTIME_DATABASE_URL", "postgresql+asyncpg://app_user:app_password@localhost:5433/gym_test")
SYNC_TEST_DATABASE_URL = TEST_DATABASE_URL.replace("+asyncpg", "")

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Run Alembic migrations once per session."""
    env = os.environ.copy()
    env["PGPASSWORD"] = "postgres"
    env["DATABASE_URL"] = TEST_DATABASE_URL
    subprocess.run(["psql", "-U", "postgres", "-h", "localhost", "-p", "5433", "-d", "gym_test", "-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;"], env=env, check=True)
    
    # Run migrations
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], env=env, check=True)
    yield

@pytest_asyncio.fixture(scope="function")
async def pg_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Ensure app_user exists and has rights
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP OWNED BY app_user CASCADE;"))
            await conn.execute(text("DROP ROLE IF EXISTS app_user;"))
    except Exception:
        pass

    async with engine.begin() as conn:
        await conn.execute(text("CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password' NOSUPERUSER NOBYPASSRLS;"))
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO app_user;"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;"))
        await conn.execute(text("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;"))
        await conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;"))
        await conn.execute(text("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO app_user;"))
        
    yield engine
    
    # Cleanup data (truncate all tables) after each test
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            try:
                await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE;"))
            except Exception:
                pass
            
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def pg_session_maker(pg_engine):
    runtime_engine = create_async_engine(TEST_RUNTIME_DATABASE_URL, echo=False)
    yield async_sessionmaker(runtime_engine, class_=AsyncSession, expire_on_commit=False)
    await runtime_engine.dispose()
