from fastapi import Header, HTTPException, Request, Depends
from typing import Optional
from uuid import UUID
import contextvars

from app.core.security import get_session_token_from_cookie

# Context variable to hold the current tenant ID for the request
current_tenant_id_var: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "current_tenant_id", default=None
)

def get_tenant_id(x_tenant_id: str = Header(..., alias="X-Tenant-ID")) -> UUID:
    """Dependency to extract and validate the X-Tenant-ID header."""
    try:
        tenant_id = UUID(x_tenant_id)
        current_tenant_id_var.set(tenant_id)
        return tenant_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-ID header format. Must be a UUID.")

def get_current_session_token(request: Request) -> str:
    """
    Dependency that enforces authentication via Secure HttpOnly cookie.
    """
    token = get_session_token_from_cookie(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token

async def get_current_user(token: str = Depends(get_current_session_token)) -> dict:
    """
    Placeholder for retrieving the current user from the session token.
    """
    # TODO: Query database to find UserSession by token_hash and return User
    return {"user_id": "dummy-user-id"}
