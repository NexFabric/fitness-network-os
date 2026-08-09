from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.entitlement import EntitlementService

router = APIRouter()

class EntitlementConsumeRequest(BaseModel):
    action: str

class EntitlementConsumeResponse(BaseModel):
    granted: bool
    last_known_state: str
    offline_ttl_hours: int | None = None
    reason: str | None = None

@router.post("/{member_id}/entitlements/consume", response_model=EntitlementConsumeResponse)
async def consume_entitlement(
    member_id: UUID,
    request: EntitlementConsumeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await EntitlementService.check_access(db, member_id, action=request.action)
    
    response = EntitlementConsumeResponse(
        granted=result["granted"],
        last_known_state=result["last_known_state"],
        offline_ttl_hours=result.get("offline_ttl_hours"),
        reason=result.get("reason")
    )
    
    if not result["granted"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=response.model_dump()
        )
        
    return response
