"""Phase 16 report HTTP surface (definitions + runs)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService
from app.models.user import User
from app.services.report import ReportService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    """Tenant-scoped staff permission check (non-:self)."""
    AuthorizationService.require_tenant(user, permission, tenant_id)


# ----- schemas -----


class DefinitionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    report_type: str = Field(default="GENERIC", max_length=100)
    description: str | None = None
    config: dict[str, Any] | None = None


class DefinitionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None
    report_type: str
    config: dict[str, Any]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RunRequest(BaseModel):
    definition_code: str = Field(min_length=1, max_length=100)
    parameters: dict[str, Any] | None = None
    export_format: str = Field(default="JSON", max_length=32)
    dedupe_key: str | None = Field(default=None, max_length=255)


class RunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    definition_id: UUID
    status: str
    result_url: str | None
    export_format: str | None
    row_count: int | None
    error_message: str | None
    parameters: dict[str, Any] | None
    requested_by_user_id: UUID | None
    dedupe_key: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    created: bool | None = None

    model_config = {"from_attributes": True}


def _run_response(row, *, created: bool | None = None) -> RunResponse:
    return RunResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        definition_id=row.definition_id,
        status=row.status,
        result_url=row.result_url,
        export_format=row.export_format,
        row_count=row.row_count,
        error_message=row.error_message,
        parameters=row.parameters,
        requested_by_user_id=row.requested_by_user_id,
        dedupe_key=row.dedupe_key,
        started_at=row.started_at,
        finished_at=row.finished_at,
        created_at=row.created_at,
        created=created,
    )


# ----- definitions -----


@router.post("/definitions", response_model=DefinitionResponse, status_code=201)
async def create_definition(
    body: DefinitionCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "reports:write")
    svc = ReportService(db)
    try:
        row = await svc.create_definition(
            tenant_id,
            code=body.code,
            name=body.name,
            report_type=body.report_type,
            description=body.description,
            config=body.config,
        )
        await db.commit()
        await db.refresh(row)
        return row
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/definitions", response_model=list[DefinitionResponse])
async def list_definitions(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    _require(current_user, tenant_id, "reports:read")
    return await ReportService(db).list_definitions(tenant_id, limit=limit)


# ----- runs -----


@router.post("/runs", response_model=RunResponse, status_code=201)
async def request_run(
    body: RunRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "reports:run")
    svc = ReportService(db)
    try:
        result = await svc.request_run(
            tenant_id,
            definition_code=body.definition_code,
            parameters=body.parameters,
            export_format=body.export_format,
            dedupe_key=body.dedupe_key,
            requested_by_user_id=current_user.id,
            enqueue_outbox=True,
        )
        await db.commit()
        await db.refresh(result.run)
        return _run_response(result.run, created=result.created)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "reports:read")
    row = await ReportService(db).get_run(tenant_id, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run_not_found")
    return _run_response(row)
