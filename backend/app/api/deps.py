import contextvars
from datetime import UTC
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_session_token_from_cookie
from app.db.session import get_db
from app.models.rbac import Role, UserRole
from app.models.user import User, UserSession

# Context variable to hold the current tenant ID for the request
current_tenant_id_var: contextvars.ContextVar[UUID | None] = contextvars.ContextVar(
    "current_tenant_id", default=None
)

def get_current_session_token(request: Request) -> str:
    """
    Dependency that enforces authentication via Secure HttpOnly cookie.
    """
    token = get_session_token_from_cookie(request)
    
    # Fallback to Authorization: Bearer header for mobile apps and tests
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
    import hashlib
    from datetime import datetime
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    result = await db.execute(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.is_revoked == False,
            UserSession.expires_at > datetime.now(UTC)
        )
    )
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
        
    from sqlalchemy.orm import selectinload
    result_user = await db.execute(
        select(User)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions)
        )
        .where(User.id == session.user_id)
    )
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
        await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}';"))
        return tenant_id

    # Temporarily set the RLS context so we can read the UserRole for this tenant
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}';"))
    
    # Verify user belongs to the requested tenant via UserRole
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.tenant_id == tenant_id
        )
    )
    user_role = result.scalars().first()
    
    if not user_role:
        # Reset RLS if unauthorized
        await db.execute(text("SET LOCAL app.current_tenant_id = '';"))
        raise HTTPException(status_code=403, detail="User does not have access to this tenant")
        
    current_tenant_id_var.set(tenant_id)
    return tenant_id
