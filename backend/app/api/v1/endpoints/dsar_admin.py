"""Staff view of tenant DSAR requests. Does not widen RLS."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.dsar import DsarService

router = APIRouter()


class AdminDsarResponse(BaseModel):
    id: UUID
    member_id: UUID
    kind: str
    status: str
    due_at: datetime
    download_url: str | None = None
    rejection_reason: str | None = None

    model_config = ConfigDict(from_attributes=True)


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


@router.get("", response_model=list[AdminDsarResponse])
async def list_dsar(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:read:all")
    svc = DsarService(db)
    rows = await svc.list_for_tenant(tenant_id)
    out: list[AdminDsarResponse] = []
    for row in rows:
        out.append(
            AdminDsarResponse(
                id=row.id,
                member_id=row.member_id,
                kind=row.kind,
                status=row.status,
                due_at=row.due_at,
                download_url=await svc.download_url(tenant_id, row),
                rejection_reason=row.rejection_reason,
            )
        )
    return out


@router.get("/{request_id}", response_model=AdminDsarResponse)
async def get_dsar(
    request_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:read:all")
    svc = DsarService(db)
    row = await svc.get(tenant_id, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="dsar_not_found")
    return AdminDsarResponse(
        id=row.id,
        member_id=row.member_id,
        kind=row.kind,
        status=row.status,
        due_at=row.due_at,
        download_url=await svc.download_url(tenant_id, row),
        rejection_reason=row.rejection_reason,
    )
