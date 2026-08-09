"""Member self-service routes — never accept caller-controlled member_id.

Pattern matches POST /access/qr/issue-self (Phase 15.5B/C):
current_user.id → members.user_id binding → server-owned member_id.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, StrictInt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.entitlement import EntitlementService
from app.services.member import MemberService

router = APIRouter()

StrictQty = Annotated[StrictInt, Field(ge=1)]


class MeEntitlementCheckRequest(BaseModel):
    action: str
    quantity: StrictQty = 1


class MeEntitlementAccessResponse(BaseModel):
    granted: bool
    last_known_state: str
    offline_ttl_hours: int | None = None
    reason: str | None = None
    remaining: int | None = None
    member_id: UUID


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


@router.post(
    "/entitlements/check",
    response_model=MeEntitlementAccessResponse,
)
async def check_my_entitlement(
    body: MeEntitlementCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Self entitlement check: entitlements:check:self only; no path member_id."""
    _require(current_user, tenant_id, "entitlements:check:self")
    member = await MemberService(db).get_member_by_user_id(tenant_id, current_user.id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="member_not_bound",
        )
    result = await EntitlementService.check_access(
        db, tenant_id, member.id, body.action, body.quantity
    )
    return MeEntitlementAccessResponse(
        granted=result["granted"],
        last_known_state=result["last_known_state"],
        offline_ttl_hours=result.get("offline_ttl_hours"),
        reason=result.get("reason"),
        remaining=result.get("remaining"),
        member_id=member.id,
    )
