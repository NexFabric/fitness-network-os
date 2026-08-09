from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.outbox import OutboxService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


class OutboxEnqueueRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=255)
    payload: dict
    aggregate_type: str | None = None
    aggregate_id: UUID | None = None
    dedupe_key: str | None = None


class OutboxEventResponse(BaseModel):
    id: UUID
    event_type: str
    status: str
    attempt_count: int
    dedupe_key: str | None
    created_at: datetime
    created: bool | None = None

    model_config = {"from_attributes": True}


class InboxReceiveRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=255)
    event_type: str = Field(min_length=1, max_length=255)
    payload: dict


class InboxReceiveResponse(BaseModel):
    id: UUID
    event_id: str
    event_type: str
    status: str
    is_duplicate: bool


class DispatchResponse(BaseModel):
    published: int
    failed: int


@router.post("/events", response_model=OutboxEventResponse, status_code=201)
async def enqueue_outbox(
    body: OutboxEnqueueRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "outbox:write")
    svc = OutboxService(db)
    try:
        result = await svc.enqueue(
            tenant_id,
            body.event_type,
            body.payload,
            aggregate_type=body.aggregate_type,
            aggregate_id=body.aggregate_id,
            dedupe_key=body.dedupe_key,
        )
        await db.commit()
        await db.refresh(result.event)
        return OutboxEventResponse(
            id=result.event.id,
            event_type=result.event.event_type,
            status=result.event.status,
            attempt_count=result.event.attempt_count,
            dedupe_key=result.event.dedupe_key,
            created_at=result.event.created_at,
            created=result.created,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_outbox(
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """Claim and mark-publish (dev/ops sink — real transports later)."""
    _require(current_user, tenant_id, "outbox:dispatch")
    svc = OutboxService(db)
    claimed = await svc.claim_pending(tenant_id=tenant_id, limit=limit)

    async def _noop_publish(ev) -> None:
        return None

    stats = await svc.dispatch_claimed(claimed, _noop_publish)
    await db.commit()
    return DispatchResponse(**stats)


@router.post("/inbox", response_model=InboxReceiveResponse, status_code=201)
async def receive_inbox(
    body: InboxReceiveRequest,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "inbox:write")
    svc = OutboxService(db)
    try:
        result = await svc.receive_inbox(
            tenant_id,
            event_id=body.event_id,
            event_type=body.event_type,
            payload=body.payload,
        )
        await db.commit()
        await db.refresh(result.event)
        return InboxReceiveResponse(
            id=result.event.id,
            event_id=result.event.event_id,
            event_type=result.event.event_type,
            status=result.event.status,
            is_duplicate=result.is_duplicate,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
