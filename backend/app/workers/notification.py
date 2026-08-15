import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant, TenantStatus
from app.services.notification import NotificationService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("notification-worker")


async def run_worker() -> None:
    logger.info("Starting Notification Worker")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Process only for ACTIVE tenants
                tenants_res = await db.execute(
                    select(Tenant).where(Tenant.status == TenantStatus.ACTIVE)
                )
                tenants = tenants_res.scalars().all()

                processed_any = False
                for tenant in tenants:
                    service = NotificationService(db)
                    res = await service.process_due_failed(
                        tenant_id=tenant.id, limit=20
                    )
                    sent_count = res.get("sent", 0) if isinstance(res, dict) else 0
                    failed_count = res.get("failed", 0) if isinstance(res, dict) else 0
                    if sent_count > 0 or failed_count > 0:
                        processed_any = True
                        logger.info(f"Processed notifications for {tenant.id}: {res}")

                # Commit all notification delivery states
                await db.commit()

                if not processed_any:
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error in notification worker loop: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
