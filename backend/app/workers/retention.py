import asyncio
import logging

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_tenant_id_var
from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant, TenantStatus
from app.services.retention import DataRetentionService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("retention-worker")


async def run_retention_sweep(db_override: AsyncSession | None = None) -> int:
    """Executes a single retention sweep across all active tenants."""
    total_affected = 0

    async def _sweep(db: AsyncSession) -> int:
        nonlocal total_affected
        tenants_res = await db.execute(
            select(Tenant).where(Tenant.status == TenantStatus.ACTIVE)
        )
        tenants = list(tenants_res.scalars().all())

        for tenant in tenants:
            token = current_tenant_id_var.set(tenant.id)
            if db.bind and db.bind.dialect.name == "postgresql":
                await db.execute(
                    text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                    {"tid": str(tenant.id)},
                )
            try:
                service = DataRetentionService(db)
                stats = await service.enforce_policies_for_tenant(tenant.id)
                affected = sum(stats.values())
                if affected > 0:
                    total_affected += affected
                    logger.info(
                        f"Retention sweep completed for tenant {tenant.id}: {stats}"
                    )
                await db.commit()
            except Exception:
                logger.exception(
                    "Error in retention sweep for tenant %s", tenant.id
                )
                await db.rollback()
            finally:
                current_tenant_id_var.reset(token)
                if db.bind and db.bind.dialect.name == "postgresql":
                    await db.execute(
                        text("SELECT set_config('app.current_tenant_id', '', true)")
                    )

        return total_affected

    if db_override is not None:
        return await _sweep(db_override)

    async with AsyncSessionLocal() as db:
        return await _sweep(db)


async def run_worker() -> None:
    logger.info("Starting Data Retention Worker")
    from app.core.metrics import WORKER_HEARTBEAT, start_worker_metrics_server

    start_worker_metrics_server()
    while True:
        try:
            affected = await run_retention_sweep()
            WORKER_HEARTBEAT.labels(worker="retention").set_to_current_time()
            if affected > 0:
                logger.info(f"Total retention records processed: {affected}")
            # Sleep 1 hour between retention sweeps
            await asyncio.sleep(3600)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in retention worker loop: {e}")
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(run_worker())
