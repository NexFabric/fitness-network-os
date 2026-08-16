import asyncio
import logging

from sqlalchemy import select, text

from app.api.deps import current_tenant_id_var
from app.core.metrics import NOTIFICATION_DISPATCH, WORKER_HEARTBEAT, start_worker_metrics_server
from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant, TenantStatus
from app.services.notification import NotificationService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("notification-worker")


async def run_cycle() -> int:
    """Retry due/failed deliveries for every ACTIVE tenant. Returns sent+failed."""
    processed = 0
    async with AsyncSessionLocal() as db:
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
                service = NotificationService(db)
                res = await service.process_due_failed(tenant_id=tenant.id, limit=20)
                sent_count = res.get("sent", 0) if isinstance(res, dict) else 0
                failed_count = res.get("failed", 0) if isinstance(res, dict) else 0
                processed += sent_count + failed_count
                if sent_count > 0 or failed_count > 0:
                    logger.info("Processed notifications for %s: %s", tenant.id, res)
                if sent_count:
                    NOTIFICATION_DISPATCH.labels(
                        channel="all", outcome="sent"
                    ).inc(sent_count)
                if failed_count:
                    NOTIFICATION_DISPATCH.labels(
                        channel="all", outcome="failed"
                    ).inc(failed_count)
                # Commit per tenant to release row locks and isolate failure
                await db.commit()
            except Exception:
                logger.exception(
                    "Error processing notifications for tenant %s", tenant.id
                )
                await db.rollback()
            finally:
                current_tenant_id_var.reset(token)
                if db.bind and db.bind.dialect.name == "postgresql":
                    await db.execute(
                        text("SELECT set_config('app.current_tenant_id', '', true)")
                    )
    return processed


async def run_worker() -> None:
    logger.info("Starting Notification Worker")
    start_worker_metrics_server()
    while True:
        try:
            processed = await run_cycle()
            WORKER_HEARTBEAT.labels(worker="notification").set_to_current_time()
            if processed == 0:
                await asyncio.sleep(5)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in notification worker loop: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
