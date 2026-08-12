import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.tenant import Tenant
from app.services.notification import NotificationService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("notification-worker")

async def run_worker():
    logger.info("Starting Notification Worker")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Need to process per tenant. Let's get all tenants first.
                tenants_res = await db.execute(select(Tenant))
                tenants = tenants_res.scalars().all()
                
                processed_any = False
                for tenant in tenants:
                    service = NotificationService(db)
                    res = await service.process_due_failed(tenant_id=tenant.id, limit=20)
                    if getattr(res, 'get', lambda x: 0)('sent', 0) > 0 or getattr(res, 'get', lambda x: 0)('failed', 0) > 0:
                        processed_any = True
                        logger.info(f"Processed notifications for {tenant.id}: {res}")
                
                if not processed_any:
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error in notification worker loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_worker())
