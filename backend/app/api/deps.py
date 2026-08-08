from fastapi import Header, HTTPException, Request, Depends
from typing import Optional
from uuid import UUID
import contextvars
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_session_token_from_cookie
from app.db.session import get_db
from app.models.user import User, UserSession
from app.models.rbac import UserRole

# Context variable to hold the current tenant ID for the request
current_tenant_id_var: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "current_tenant_id", default=None
)

def get_current_session_token(request: Request) -> str:
    """
    Dependency that enforces authentication via Secure HttpOnly cookie.
    """
    token = get_session_token_from_cookie(request)
    # Stub: if no token in cookie, look in Authorization header for testing
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token

async def get_current_user(
    token: str = Depends(get_current_session_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Retrieve the current user from the session token.
    """
    result = await db.execute(
        select(UserSession).where(UserSession.token_hash == token).where(UserSession.is_revoked == False)
    )
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
        
    result_user = await db.execute(select(User).where(User.id == session.user_id))
    user = result_user.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive or not found")
        
    return user

async def get_tenant_id(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UUID:
    """Dependency to extract and validate the X-Tenant-ID header."""
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-ID header format. Must be a UUID.")
        
    if user.is_superuser:
        current_tenant_id_var.set(tenant_id)
        return tenant_id

    # Verify user belongs to the requested tenant via UserRole
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.tenant_id == tenant_id
        )
    )
    user_role = result.scalars().first()
    
    if not user_role:
        raise HTTPException(status_code=403, detail="User does not have access to this tenant")
        
    current_tenant_id_var.set(tenant_id)
    return tenant_id
