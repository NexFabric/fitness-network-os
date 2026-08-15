import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_tenant_id_var
from app.core.event_types import (
    NOTIFICATION_REQUESTED_V1,
    REPORT_RUN_REQUESTED_V1,
)
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
    """Dispatches claimed outbox event to registered domain handlers with RLS context.

    If the handler raises an exception, the caller (dispatch_claimed)
    will catch it and transition the outbox event to FAILED / DEAD with retry backoff.
    """
    tenant_id = getattr(event, "tenant_id", None)
    token = None
    if tenant_id:
        token = current_tenant_id_var.set(tenant_id)
        if db.bind and db.bind.dialect.name == "postgresql":
            await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}';"))

    try:
        handler = OUTBOX_EVENT_HANDLERS.get(event.event_type)
        if handler:
            logger.info(
                f"Dispatching outbox event {event.id} ({event.event_type}) for tenant {event.tenant_id}"
            )
            await handler(db, event)
        else:
            # Broadcast / log domain integration event (e.g. membership.activated.v1)
            logger.info(
                f"Published domain event {event.id} ({event.event_type}) for tenant {event.tenant_id}"
            )
    finally:
        if token is not None:
            current_tenant_id_var.reset(token)
            if db.bind and db.bind.dialect.name == "postgresql":
                await db.execute(text("SET LOCAL app.current_tenant_id = '';"))


async def run_worker() -> None:
    logger.info("Starting Outbox & Inbox Worker")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                service = OutboxService(db)

                # 1. Process Outbox Events for ACTIVE tenants
                claimed = await service.claim_pending(
                    limit=20, worker_id="outbox-worker-prod"
                )
                if claimed:
                    logger.info(f"Claimed {len(claimed)} outbox events")
                    valid_claimed: list[OutboxEvent] = []
                    for event in claimed:
                        if getattr(event, "tenant_id", None):
                            t_result = await db.execute(
                                select(Tenant).where(Tenant.id == event.tenant_id)
                            )
                            t = t_result.scalars().first()
                            if t and t.status != TenantStatus.ACTIVE:
                                logger.warning(
                                    f"Skipping outbox event {event.id} for non-ACTIVE tenant {event.tenant_id}"
                                )
                                continue
                        valid_claimed.append(event)

                    if valid_claimed:

                        async def _publisher(ev: OutboxEvent) -> None:
                            await domain_event_publisher(db, ev)

                        await service.dispatch_claimed(
                            events=valid_claimed,
                            publisher=_publisher,
                            worker_id="outbox-worker-prod",
                        )

                # 2. Process Pending Inbox Events per ACTIVE tenant with RLS context
                tenants_res = await db.execute(
                    select(Tenant).where(Tenant.status == TenantStatus.ACTIVE)
                )
                active_tenants = list(tenants_res.scalars().all())

                inbox_processed_total = 0
                for t in active_tenants:
                    token = current_tenant_id_var.set(t.id)
                    if db.bind and db.bind.dialect.name == "postgresql":
                        await db.execute(
                            text(f"SET LOCAL app.current_tenant_id = '{t.id}';")
                        )
                    try:
                        inbox_res = await service.process_pending_inbox(
                            tenant_id=t.id,
                            handlers=INBOX_HANDLERS,
                            limit=20,
                        )
                        inbox_processed_total += inbox_res.get("processed", 0)
                    finally:
                        current_tenant_id_var.reset(token)
                        if db.bind and db.bind.dialect.name == "postgresql":
                            await db.execute(
                                text("SET LOCAL app.current_tenant_id = '';")
                            )

                if inbox_processed_total > 0:
                    logger.info(
                        f"Processed {inbox_processed_total} inbox events across active tenants"
                    )

                # Commit all status updates for this batch iteration
                await db.commit()

                if not claimed and inbox_processed_total == 0:
                    await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error in outbox worker loop: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
