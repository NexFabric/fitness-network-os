import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.outbox import OutboxEvent
from app.models.tenant import Tenant, TenantStatus
from app.services.outbox import OutboxService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("outbox-worker")


async def domain_event_publisher(event: OutboxEvent) -> None:
    """Dispatches claimed outbox event to external integrations / domain subscribers.

    If an external service or transport raises an exception, the caller (dispatch_claimed)
    will catch it and transition the outbox event to FAILED / DEAD with retry backoff.
    """
    logger.info(
        f"Publishing outbox event {event.id} ({event.event_type}) for tenant {event.tenant_id}"
    )


# Default registered inbox handlers (e.g. payment webhooks, external synchronization)
INBOX_HANDLERS: dict = {}


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
                        await service.dispatch_claimed(
                            events=valid_claimed,
                            publisher=domain_event_publisher,
                            worker_id="outbox-worker-prod",
                        )

                # 2. Process Pending Inbox Events per ACTIVE tenant
                tenants_res = await db.execute(
                    select(Tenant).where(Tenant.status == TenantStatus.ACTIVE)
                )
                active_tenants = list(tenants_res.scalars().all())

                inbox_processed_total = 0
                for t in active_tenants:
                    inbox_res = await service.process_pending_inbox(
                        tenant_id=t.id,
                        handlers=INBOX_HANDLERS,
                        limit=20,
                    )
                    inbox_processed_total += inbox_res.get("processed", 0)

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
