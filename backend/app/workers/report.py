import asyncio
import logging

from sqlalchemy import select, text

from app.api.deps import current_tenant_id_var
from app.db.session import AsyncSessionLocal
from app.models.report import REPORT_STATUS_PENDING, ReportRun
from app.models.tenant import Tenant, TenantStatus
from app.services.report import ReportService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("report-worker")


async def run_cycle() -> int:
    """Execute pending report runs for every ACTIVE tenant. Returns how many ran."""
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
                runs_res = await db.execute(
                    select(ReportRun)
                    .where(
                        ReportRun.tenant_id == tenant.id,
                        ReportRun.status == REPORT_STATUS_PENDING,
                    )
                    .with_for_update(skip_locked=True)
                    .limit(10)
                )
                runs = list(runs_res.scalars().all())
                for run in runs:
                    service = ReportService(db)
                    logger.info(
                        f"Executing report run {run.id} for tenant {tenant.id}"
                    )
                    await service.execute_run(tenant.id, run.id)
                    processed += 1
            finally:
                current_tenant_id_var.reset(token)
                if db.bind and db.bind.dialect.name == "postgresql":
                    await db.execute(text("SET LOCAL app.current_tenant_id = '';"))
        await db.commit()
    return processed


async def run_worker() -> None:
    logger.info("Starting Report Worker")
    while True:
        try:
            processed = await run_cycle()
            if processed == 0:
                await asyncio.sleep(5)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in report worker loop: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
