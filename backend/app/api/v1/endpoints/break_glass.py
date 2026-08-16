from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_recent_step_up
from app.core.authorization import AuthorizationService
from app.models.break_glass import BreakGlassSession, BreakGlassStatus
from app.models.user import User
from app.services.break_glass import BreakGlassService

router = APIRouter()


class CreateBreakGlassRequest(BaseModel):
    target_tenant_id: UUID
    reason: str = Field(..., min_length=10, max_length=1000)
    ticket_reference: str = Field(..., min_length=3, max_length=100)
    duration_minutes: int = Field(default=30, ge=5, le=60)


class BreakGlassSessionResponse(BaseModel):
    id: UUID
    actor_id: UUID
    target_tenant_id: UUID
    reason: str
    ticket_reference: str
    status: BreakGlassStatus
    granted_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None

    class Config:
        from_attributes = True


def _require_break_glass_auth(current_user: User) -> None:
    if current_user.is_superuser:
        return
    if AuthorizationService.is_authorized(
        user=current_user,
        permission="admin:break_glass",
        resource_tenant_id=None,
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Bu işlem yalnızca platform süper yöneticisi veya break-glass izni olan hesap tarafından yapılabilir.",
    )


@router.post("/sessions", response_model=BreakGlassSessionResponse)
async def create_break_glass_session(
    body: CreateBreakGlassRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_recent_step_up),
):
    """Create a time-limited emergency access break-glass session for a tenant."""
    _require_break_glass_auth(current_user)

    service = BreakGlassService(db)
    session = await service.create_session(
        actor_id=current_user.id,
        target_tenant_id=body.target_tenant_id,
        reason=body.reason,
        ticket_reference=body.ticket_reference,
        duration_minutes=body.duration_minutes,
    )
    return session


@router.get("/sessions", response_model=list[BreakGlassSessionResponse])
async def list_break_glass_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent break-glass sessions for platform auditing."""
    _require_break_glass_auth(current_user)

    # Auto-expire any stale sessions first
    service = BreakGlassService(db)
    await service.expire_stale_sessions()

    result = await db.execute(
        select(BreakGlassSession)
        .order_by(BreakGlassSession.granted_at.desc())
        .limit(50)
    )
    return list(result.scalars().all())


@router.post("/sessions/{session_id}/revoke", response_model=BreakGlassSessionResponse)
async def revoke_break_glass_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke an active break-glass emergency access session immediately."""
    _require_break_glass_auth(current_user)

    service = BreakGlassService(db)
    session = await service.revoke_session(
        session_id=session_id, actor_id=current_user.id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Acil durum erişim oturumu bulunamadı.",
        )
    return session
