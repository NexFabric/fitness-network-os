from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService
from app.models.data_import import (
    DataImportBatch,
    DataImportRow,
    ImportBatchStatus,
    ImportRowStatus,
)
from app.models.user import User
from app.services.data_import import DataImportService

router = APIRouter()


class ImportBatchResponse(BaseModel):
    id: UUID
    filename: str
    status: ImportBatchStatus
    total_rows: int
    valid_rows: int
    invalid_rows: int
    imported_rows: int
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class ImportRowResponse(BaseModel):
    id: UUID
    row_number: int
    status: ImportRowStatus
    raw_data: dict
    parsed_data: dict | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


class ImportBatchDetailResponse(ImportBatchResponse):
    rows: list[ImportRowResponse]


class CsvUploadRequest(BaseModel):
    filename: str = "members.csv"
    csv_content: str


@router.post("/upload", response_model=ImportBatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv_preview(
    req: CsvUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Upload CSV member migration file to create validation preview batch."""
    AuthorizationService.require_tenant(current_user, "members:write", tenant_id)

    if not req.csv_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV içeriği boş olamaz.",
        )

    try:
        batch = await DataImportService.create_preview_batch(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user.id,
            filename=req.filename or "members.csv",
            csv_text=req.csv_content,
        )
        return batch
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/batches", response_model=list[ImportBatchResponse])
async def list_import_batches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List all CSV migration batches for this tenant."""
    AuthorizationService.require_tenant(current_user, "members:read", tenant_id)

    res = await db.execute(
        select(DataImportBatch)
        .where(DataImportBatch.tenant_id == tenant_id)
        .order_by(DataImportBatch.created_at.desc())
    )
    return list(res.scalars().all())


@router.get("/batch/{batch_id}", response_model=ImportBatchDetailResponse)
async def get_import_batch_detail(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get single import batch and its detailed rows & validation errors."""
    AuthorizationService.require_tenant(current_user, "members:read", tenant_id)

    batch = await db.get(DataImportBatch, batch_id)
    if not batch or batch.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İçe aktarma grubu bulunamadı.",
        )

    rows_res = await db.execute(
        select(DataImportRow)
        .where(
            DataImportRow.batch_id == batch_id,
            DataImportRow.tenant_id == tenant_id,
        )
        .order_by(DataImportRow.row_number)
    )
    rows = list(rows_res.scalars().all())

    return ImportBatchDetailResponse(
        id=batch.id,
        filename=batch.filename,
        status=batch.status,
        total_rows=batch.total_rows,
        valid_rows=batch.valid_rows,
        invalid_rows=batch.invalid_rows,
        imported_rows=batch.imported_rows,
        created_at=batch.created_at,
        completed_at=batch.completed_at,
        rows=rows,
    )


@router.post("/batch/{batch_id}/commit", response_model=ImportBatchResponse)
async def commit_import_batch(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Execute transactional import of all valid rows in batch into members table."""
    AuthorizationService.require_tenant(current_user, "members:write", tenant_id)

    try:
        batch = await DataImportService.commit_batch(
            db=db,
            tenant_id=tenant_id,
            batch_id=batch_id,
        )
        return batch
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
