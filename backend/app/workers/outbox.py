import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_tenant_id_var
from app.core.event_types import (
    NOTIFICATION_REQUESTED_V1,
    REPORT_RUN_REQUESTED_V1,
)
from app.core.metrics import WORKER_HEARTBEAT, start_worker_metrics_server
from app.db.session import AsyncSessionLocal
from app.models.outbox import OutboxEvent
from app.models.tenant import Tenant, TenantStatus
from app.services.notification import outbox_notification_requested_handler
from app.services.outbox import OutboxService
from app.services.report import outbox_report_run_requested_handler

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("outbox-worker")

# Registered domain handlers for outbox event execution
OUTBOX_EVENT_HANDLERS: dict[str, Callable[[AsyncSession, Any], Awaitable[None]]] = {
    NOTIFICATION_REQUESTED_V1: outbox_notification_requested_handler,
    REPORT_RUN_REQUESTED_V1: outbox_report_run_requested_handler,
}

# Default registered inbox handlers (e.g. payment webhooks, external synchronization)
INBOX_HANDLERS: dict[str, Any] = {}


async def domain_event_publisher(db: AsyncSession, event: OutboxEvent) -> None:
    """Dispatches claimed outbox event to registered domain handlers with nested savepoint.

    Uses a nested savepoint (`begin_nested`) so that any SQL error or unhandled
    exception inside the domain handler is rolled back to the savepoint.
    This leaves the outer transaction valid so OutboxService.mark_failed
    can record the failure / retry status in outbox_events.
    """
    handler = OUTBOX_EVENT_HANDLERS.get(event.event_type)
    if handler:
        logger.info(
            f"Dispatching outbox event {event.id} ({event.event_type}) for tenant {event.tenant_id}"
        )
        async with db.begin_nested():
            await handler(db, event)
    else:
        # Broadcast / log domain integration event (e.g. membership.activated.v1)
        logger.info(
            f"Published domain event {event.id} ({event.event_type}) for tenant {event.tenant_id}"
        )


async def process_outbox_for_tenant(
    db: AsyncSession,
    tenant_id: UUID,
    *,
    worker_id: str = "outbox-worker-prod",
    batch_limit: int = 20,
) -> dict[str, int]:
    """Processes outbox events for a single tenant with RLS context established."""
    service = OutboxService(db)
    claimed = await service.claim_pending(
        tenant_id=tenant_id,
        limit=batch_limit,
        worker_id=worker_id,
    )
    if not claimed:
        return {"claimed": 0, "published": 0, "failed": 0}

    logger.info(f"Claimed {len(claimed)} outbox events for tenant {tenant_id}")

    async def _publisher(ev: OutboxEvent) -> None:
        await domain_event_publisher(db, ev)

    dispatch_stats = await service.dispatch_claimed(
        events=claimed,
        publisher=_publisher,
        worker_id=worker_id,
    )
    return {
        "claimed": len(claimed),
        "published": dispatch_stats.get("published", 0),
        "failed": dispatch_stats.get("failed", 0),
    }


async def run_outbox_cycle(
    db: AsyncSession,
    *,
    worker_id: str = "outbox-worker-prod",
    batch_limit: int = 20,
) -> dict[str, int]:
    """Executes a complete outbox & inbox cycle across all ACTIVE tenants with RLS isolation."""
    service = OutboxService(db)
    tenants_res = await db.execute(
        select(Tenant).where(Tenant.status == TenantStatus.ACTIVE)
    )
    active_tenants = list(tenants_res.scalars().all())

    outbox_published_total = 0
    outbox_failed_total = 0
    inbox_processed_total = 0

    for t in active_tenants:
        token = current_tenant_id_var.set(t.id)
        if db.bind and db.bind.dialect.name == "postgresql":
            await db.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": str(t.id)},
            )
        try:
            # 1. Process Outbox Events for this tenant
            obx_stats = await process_outbox_for_tenant(
                db, t.id, worker_id=worker_id, batch_limit=batch_limit
            )
            outbox_published_total += obx_stats.get("published", 0)
            outbox_failed_total += obx_stats.get("failed", 0)

            # 2. Process Pending Inbox Events for this tenant
            inbox_res = await service.process_pending_inbox(
                tenant_id=t.id,
                handlers=INBOX_HANDLERS,
                limit=batch_limit,
            )
            inbox_processed_total += inbox_res.get("processed", 0)

            # Commit per tenant to isolate progress and release row locks
            await db.commit()
        except Exception:
            logger.exception(f"Error in outbox cycle for tenant {t.id}")
            await db.rollback()
        finally:
            current_tenant_id_var.reset(token)
            if db.bind and db.bind.dialect.name == "postgresql":
                await db.execute(
                    text("SELECT set_config('app.current_tenant_id', '', true)")
                )

    return {
        "outbox_published": outbox_published_total,
        "outbox_failed": outbox_failed_total,
        "inbox_processed": inbox_processed_total,
    }


async def run_worker() -> None:
    logger.info("Starting Outbox & Inbox Worker")
    start_worker_metrics_server()
    while True:
        try:
            async with AsyncSessionLocal() as db:
                cycle_stats = await run_outbox_cycle(db)
                WORKER_HEARTBEAT.labels(worker="outbox").set_to_current_time()
                total_activity = (
                    cycle_stats["outbox_published"]
                    + cycle_stats["outbox_failed"]
                    + cycle_stats["inbox_processed"]
                )
                if total_activity == 0:
                    await asyncio.sleep(2)
        except Exception:
            logger.exception("Error in outbox worker loop")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
