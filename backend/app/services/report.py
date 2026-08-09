"""Phase 16 report service — definitions + async run lifecycle (metadata only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_types import REPORT_RUN_REQUESTED_V1
from app.core.events import is_envelope
from app.models.report import (
    REPORT_STATUS_CANCELLED,
    REPORT_STATUS_FAILED,
    REPORT_STATUS_PENDING,
    REPORT_STATUS_RUNNING,
    REPORT_STATUS_SUCCEEDED,
    ReportDefinition,
    ReportRun,
)
from app.services.outbox import OutboxService


@dataclass
class RunRequestResult:
    run: ReportRun
    created: bool


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_definition(
        self,
        tenant_id: UUID,
        *,
        code: str,
        name: str,
        report_type: str = "GENERIC",
        description: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> ReportDefinition:
        code = code.strip().lower()
        if not code or not name.strip():
            raise ValueError("code_and_name_required")
        row = ReportDefinition(
            id=uuid4(),
            tenant_id=tenant_id,
            code=code,
            name=name.strip(),
            description=description,
            report_type=report_type.strip().upper() or "GENERIC",
            config=dict(config or {}),
            is_active=True,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(row)
                await self.db.flush()
        except IntegrityError as e:
            raise ValueError("report_code_conflict") from e
        return row

    async def get_definition_by_code(
        self, tenant_id: UUID, code: str
    ) -> ReportDefinition | None:
        result = await self.db.execute(
            select(ReportDefinition).where(
                ReportDefinition.tenant_id == tenant_id,
                ReportDefinition.code == code.strip().lower(),
            )
        )
        return result.scalars().first()

    async def list_definitions(
        self, tenant_id: UUID, *, limit: int = 50
    ) -> list[ReportDefinition]:
        limit = max(1, min(limit, 200))
        result = await self.db.execute(
            select(ReportDefinition)
            .where(ReportDefinition.tenant_id == tenant_id)
            .order_by(ReportDefinition.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def request_run(
        self,
        tenant_id: UUID,
        *,
        definition_code: str,
        parameters: dict[str, Any] | None = None,
        export_format: str = "JSON",
        dedupe_key: str | None = None,
        requested_by_user_id: UUID | None = None,
        enqueue_outbox: bool = True,
    ) -> RunRequestResult:
        defn = await self.get_definition_by_code(tenant_id, definition_code)
        if defn is None or not defn.is_active:
            raise ValueError("definition_not_found")

        if dedupe_key:
            existing = await self.db.execute(
                select(ReportRun).where(
                    ReportRun.tenant_id == tenant_id,
                    ReportRun.dedupe_key == dedupe_key,
                )
            )
            found = existing.scalars().first()
            if found:
                return RunRequestResult(run=found, created=False)

        run = ReportRun(
            id=uuid4(),
            tenant_id=tenant_id,
            definition_id=defn.id,
            status=REPORT_STATUS_PENDING,
            parameters=dict(parameters or {}),
            export_format=export_format.strip().upper(),
            dedupe_key=dedupe_key,
            requested_by_user_id=requested_by_user_id,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(run)
                await self.db.flush()
        except IntegrityError:
            if dedupe_key:
                existing = await self.db.execute(
                    select(ReportRun).where(
                        ReportRun.tenant_id == tenant_id,
                        ReportRun.dedupe_key == dedupe_key,
                    )
                )
                found = existing.scalars().first()
                if found:
                    return RunRequestResult(run=found, created=False)
            raise

        if enqueue_outbox:
            await OutboxService(self.db).enqueue(
                tenant_id,
                REPORT_RUN_REQUESTED_V1,
                {
                    "run_id": str(run.id),
                    "definition_code": defn.code,
                },
                aggregate_type="report_run",
                aggregate_id=run.id,
                dedupe_key=f"report-run:{run.id}",
            )
        return RunRequestResult(run=run, created=True)

    async def execute_run(self, tenant_id: UUID, run_id: UUID) -> ReportRun:
        """MVP executor: mark SUCCESS with synthetic export URL (no file store)."""
        result = await self.db.execute(
            select(ReportRun)
            .where(ReportRun.tenant_id == tenant_id, ReportRun.id == run_id)
            .with_for_update()
        )
        run = result.scalars().first()
        if run is None:
            raise ValueError("run_not_found")
        if run.status in (REPORT_STATUS_SUCCEEDED, REPORT_STATUS_CANCELLED):
            return run

        run.status = REPORT_STATUS_RUNNING
        run.started_at = datetime.now(UTC)
        await self.db.flush()

        try:
            # Placeholder export: real exporters land in later phase
            run.row_count = 0
            run.result_url = f"memory://reports/{tenant_id}/{run.id}"
            run.status = REPORT_STATUS_SUCCEEDED
            run.finished_at = datetime.now(UTC)
            run.error_message = None
        except Exception as e:  # pragma: no cover - defensive
            run.status = REPORT_STATUS_FAILED
            run.error_message = str(e)[:2000]
            run.finished_at = datetime.now(UTC)
        await self.db.flush()
        return run

    async def get_run(self, tenant_id: UUID, run_id: UUID) -> ReportRun | None:
        result = await self.db.execute(
            select(ReportRun).where(
                ReportRun.tenant_id == tenant_id, ReportRun.id == run_id
            )
        )
        return result.scalars().first()


async def outbox_report_run_requested_handler(db: AsyncSession, event: Any) -> None:
    payload = event.payload
    if isinstance(payload, dict) and is_envelope(payload):
        data = payload["data"]
    elif isinstance(payload, dict):
        data = payload.get("data", payload)
    else:
        data = {}
    run_id = data.get("run_id") if isinstance(data, dict) else None
    if not run_id:
        raise ValueError("run_id_required")
    await ReportService(db).execute_run(event.tenant_id, UUID(str(run_id)))
