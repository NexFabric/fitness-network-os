from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.core.config import settings

engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    connect_args={
        "server_settings": {"statement_timeout": str(settings.DB_STATEMENT_TIMEOUT_MS)},
        "command_timeout": settings.DB_COMMAND_TIMEOUT,
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# RLS hook to inject current tenant into every transaction
@event.listens_for(Session, "after_begin")
def set_tenant_id(session, transaction, connection):
    # Import locally to avoid potential circular dependencies if deps imports db
    from app.api.deps import current_tenant_id_var

    tenant_id = current_tenant_id_var.get(None)
    if tenant_id and connection.dialect.name == "postgresql":
        connection.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
