from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

from app.core.config import settings

engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=False,
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
    if tenant_id and connection.dialect.name == 'postgresql':
        connection.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}';"))

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

