import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services.outbox import OutboxService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("outbox-worker")


async def dummy_publisher(event):
    # Dummy publisher for local environment
    pass


async def run_worker():
    logger.info("Starting Outbox Worker")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                service = OutboxService(db)
                claimed = await service.claim_pending(
                    limit=20, worker_id="outbox-worker-prod"
                )
                if claimed:
                    from sqlalchemy import select

                    from app.models.tenant import Tenant, TenantStatus

                    logger.info(f"Claimed {len(claimed)} outbox events")
                    valid_claimed = []
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
                            publisher=dummy_publisher,
                            worker_id="outbox-worker-prod",
                        )

                inbox_claimed = await service.process_pending_inbox(
                    limit=20, worker_id="inbox-worker-prod"
                )
                if getattr(inbox_claimed, "get", lambda x: 0)("processed", 0) > 0:
                    logger.info(f"Processed inbox events: {inbox_claimed}")

                if (
                    not claimed
                    and getattr(inbox_claimed, "get", lambda x: 0)("processed", 0) == 0
                ):
                    await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error in outbox worker loop: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
