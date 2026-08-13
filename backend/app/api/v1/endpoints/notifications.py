"""Phase 16 notification HTTP surface (templates + deliveries)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService
from app.models.notification import NotificationDelivery
from app.models.user import User
from app.services.notification import NotificationService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    """Tenant-scoped staff permission check (non-:self)."""
    AuthorizationService.require_tenant(user, permission, tenant_id)


# ----- schemas -----


class TemplateCreate(BaseModel):
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    channel: str = Field(min_length=1, max_length=50)
    body_template: str = Field(min_length=1)
    subject_template: str | None = Field(default=None, max_length=255)
    locale: str | None = Field(default=None, max_length=16)


class TemplateResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    channel: str
    subject_template: str | None
    body_template: str
    is_active: bool
    locale: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeliveryScheduleRequest(BaseModel):
    channel: str = Field(min_length=1, max_length=50)
    recipient_address: str | None = Field(default=None, max_length=512)
    recipient_user_id: UUID | None = None
    template_code: str | None = Field(default=None, max_length=100)
    subject: str | None = Field(default=None, max_length=255)
    body: str | None = None
    context: dict[str, Any] | None = None
    dedupe_key: str | None = Field(default=None, max_length=255)
    correlation_id: str | None = Field(default=None, max_length=255)
    source_event_type: str | None = Field(default=None, max_length=255)
    source_event_id: str | None = Field(default=None, max_length=255)


class DeliveryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    template_id: UUID | None
    recipient_user_id: UUID | None
    recipient_address: str | None
    channel: str
    status: str
    subject: str | None
    body: str | None
    context: dict[str, Any]
    error_message: str | None
    attempt_count: int
    available_at: datetime | None
    sent_at: datetime | None
    dedupe_key: str | None
    provider: str | None
    provider_message_id: str | None
    source_event_type: str | None
    source_event_id: str | None
    correlation_id: str | None
    created_at: datetime
    created: bool | None = None

    model_config = {"from_attributes": True}


def _delivery_response(
    row: NotificationDelivery, *, created: bool | None = None
) -> DeliveryResponse:
    return DeliveryResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        template_id=row.template_id,
        recipient_user_id=row.recipient_user_id,
        recipient_address=row.recipient_address,
        channel=row.channel,
        status=row.status,
        subject=row.subject,
        body=row.body,
        context=row.context or {},
        error_message=row.error_message,
        attempt_count=row.attempt_count,
        available_at=row.available_at,
        sent_at=row.sent_at,
        dedupe_key=row.dedupe_key,
        provider=row.provider,
        provider_message_id=row.provider_message_id,
        source_event_type=row.source_event_type,
        source_event_id=row.source_event_id,
        correlation_id=row.correlation_id,
        created_at=row.created_at,
        created=created,
    )


# ----- templates -----


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    body: TemplateCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "notifications:write")
    svc = NotificationService(db)
    try:
        row = await svc.create_template(
            tenant_id,
            code=body.code,
            name=body.name,
            channel=body.channel,
            body_template=body.body_template,
            subject_template=body.subject_template,
            locale=body.locale,
        )
        await db.commit()
        await db.refresh(row)
        return row
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    _require(current_user, tenant_id, "notifications:read")
    return await NotificationService(db).list_templates(tenant_id, limit=limit)


# ----- deliveries -----


@router.post("/deliveries", response_model=DeliveryResponse)
async def schedule_delivery(
    body: DeliveryScheduleRequest,
    response: Response,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Schedule a delivery.

    Permission policy (IR-004):
    - ``recipient_user_id`` present (tenant-bound user) → ``notifications:send``
    - free-form ``recipient_address`` only (no user_id) → ``notifications:write``
      (stricter; FRONT_DESK with send-only cannot blast arbitrary addresses)
    """
    # Free-form address alone requires write; in-tenant user target needs send.
    if body.recipient_user_id is not None:
        _require(current_user, tenant_id, "notifications:send")
    else:
        _require(current_user, tenant_id, "notifications:write")
    svc = NotificationService(db)
    try:
        result = await svc.schedule_delivery(
            tenant_id,
            channel=body.channel,
            recipient_address=body.recipient_address,
            recipient_user_id=body.recipient_user_id,
            template_code=body.template_code,
            subject=body.subject,
            body=body.body,
            context=body.context,
            dedupe_key=body.dedupe_key,
            correlation_id=body.correlation_id,
            source_event_type=body.source_event_type,
            source_event_id=body.source_event_id,
            enqueue_outbox=True,
        )
        await db.commit()
        await db.refresh(result.delivery)
        # 201 Created on first insert; 200 OK on dedupe hit (created=False)
        response.status_code = 201 if result.created else 200
        return _delivery_response(result.delivery, created=result.created)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/deliveries", response_model=list[DeliveryResponse])
async def list_deliveries(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(default=None, max_length=32),
    channel: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Recent delivery history. Read-only, so `notifications:read` is enough —
    scheduling one still needs write/send."""
    _require(current_user, tenant_id, "notifications:read")
    rows = await NotificationService(db).list_deliveries(
        tenant_id, status=status, channel=channel, limit=limit
    )
    return [_delivery_response(row) for row in rows]


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(
    delivery_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "notifications:read")
    result = await db.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.tenant_id == tenant_id,
            NotificationDelivery.id == delivery_id,
        )
    )
    row = result.scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="delivery_not_found")
    return _delivery_response(row)
