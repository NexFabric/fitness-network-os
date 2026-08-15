import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.report import REPORT_STATUS_PENDING, ReportRun
from app.models.tenant import Tenant, TenantStatus
from app.services.report import ReportService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("report-worker")


async def run_worker() -> None:
    logger.info("Starting Report Worker")
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
                    runs_res = await db.execute(
                        select(ReportRun)
                        .where(
                            ReportRun.tenant_id == tenant.id,
                            ReportRun.status == REPORT_STATUS_PENDING,
                        )
                        .limit(10)
                    )
                    runs = runs_res.scalars().all()
                    for run in runs:
                        service = ReportService(db)
                        logger.info(
                            f"Executing report run {run.id} for tenant {tenant.id}"
                        )
                        await service.execute_run(tenant.id, run.id)
                        processed_any = True

                # Commit all report run states
                await db.commit()

                if not processed_any:
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error in report worker loop: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
