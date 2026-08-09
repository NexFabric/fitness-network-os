from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.entitlement import EntitlementService

router = APIRouter()


class EntitlementCheckRequest(BaseModel):
    action: str
    quantity: int = Field(default=1, ge=1)


class EntitlementConsumeRequest(BaseModel):
    action: str
    quantity: int = Field(default=1, ge=1)


class EntitlementAccessResponse(BaseModel):
    granted: bool
    last_known_state: str
    offline_ttl_hours: int | None = None
    reason: str | None = None
    remaining: int | None = None


@router.post(
    "/{member_id}/entitlements/check",
    response_model=EntitlementAccessResponse,
)
async def check_entitlement(
    member_id: UUID,
    request: EntitlementCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    if not AuthorizationService.is_authorized(
        user=current_user,
        permission="entitlements:check",
        resource_tenant_id=tenant_id,
    ):
        raise SecurityException()

    result = await EntitlementService.check_access(
        db, tenant_id, member_id, request.action, request.quantity
    )
    return EntitlementAccessResponse(
        granted=result["granted"],
        last_known_state=result["last_known_state"],
        offline_ttl_hours=result.get("offline_ttl_hours"),
        reason=result.get("reason"),
        remaining=result.get("remaining"),
    )


@router.post(
    "/{member_id}/entitlements/consume",
    response_model=EntitlementAccessResponse,
)
async def consume_entitlement(
    member_id: UUID,
    request: EntitlementConsumeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    if not AuthorizationService.is_authorized(
        user=current_user,
        permission="entitlements:consume",
        resource_tenant_id=tenant_id,
    ):
        raise SecurityException()

    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for this operation.",
        )

    result = await EntitlementService.consume_access(
        db,
        tenant_id,
        member_id,
        request.action,
        idempotency_key,
        quantity=request.quantity,
        actor_id=current_user.id,
    )

    response = EntitlementAccessResponse(
        granted=result["granted"],
        last_known_state=result["last_known_state"],
        offline_ttl_hours=result.get("offline_ttl_hours"),
        reason=result.get("reason"),
        remaining=result.get("remaining"),
    )

    if not result["granted"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=response.model_dump(),
        )

    return response
