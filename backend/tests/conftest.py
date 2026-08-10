import os
import subprocess
from urllib.parse import urlparse

os.environ["ENVIRONMENT"] = "test"

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fitness_test_db")
TEST_RUNTIME_DATABASE_URL = os.getenv("TEST_RUNTIME_DATABASE_URL", "postgresql+asyncpg://app_user:app_password@localhost:5432/fitness_test_db")
SYNC_TEST_DATABASE_URL = TEST_DATABASE_URL.replace("+asyncpg", "")

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Run Alembic migrations once per session."""
    env = os.environ.copy()
    parsed = urlparse(TEST_DATABASE_URL)
    if parsed.password:
        env["PGPASSWORD"] = parsed.password
    env["DATABASE_URL"] = TEST_DATABASE_URL
    env["MIGRATOR_DATABASE_URL"] = TEST_DATABASE_URL
    env["ENVIRONMENT"] = "test"
    subprocess.run(["psql", SYNC_TEST_DATABASE_URL, "-c", "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = current_database();"], env=env, check=False)
    subprocess.run(["psql", SYNC_TEST_DATABASE_URL, "-c", "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO CURRENT_USER; GRANT ALL ON SCHEMA public TO public;"], env=env, check=True)
    subprocess.run(["psql", SYNC_TEST_DATABASE_URL, "-c", "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password' NOSUPERUSER NOBYPASSRLS; END IF; END $$; GRANT USAGE ON SCHEMA public TO app_user; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user; GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO app_user; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO app_user;"], env=env, check=True)
    
    # Run migrations
    subprocess.run(["uv", "run", "alembic", "upgrade", "head"], env=env, check=True)
    yield

@pytest_asyncio.fixture(scope="function")
async def pg_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        
    yield engine
    
    # Cleanup data (truncate all tables) after each test
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            try:
                async with conn.begin_nested():
                    await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE;"))
            except Exception:
                pass
            
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def pg_session_maker(pg_engine):
    runtime_engine = create_async_engine(TEST_RUNTIME_DATABASE_URL, echo=False)
    yield async_sessionmaker(runtime_engine, class_=AsyncSession, expire_on_commit=False)
    await runtime_engine.dispose()
