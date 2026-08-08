from fastapi import Depends, HTTPException, status
from typing import List, Callable
from app.api.deps import get_current_user

class SecurityException(HTTPException):
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

def require_permissions(required_permissions: List[str]) -> Callable:
    """
    Dependency generator that checks if the current user has the required permissions.
    """
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        # In a real implementation, we would fetch user's roles and permissions from DB or cache
        # e.g., user_permissions = [p.name for role in user.user_roles for p in role.permissions]
        user_permissions = current_user.get("permissions", [])
        
        # For development/stub purposes, we bypass the check if the user is a superuser
        # or if they have the specific permissions. 
        # (In reality, we'd pull from the DB context).
        if current_user.get("is_superuser"):
            return current_user

        missing = [p for p in required_permissions if p not in user_permissions]
        if missing:
            raise SecurityException(detail=f"Missing required permissions: {', '.join(missing)}")
        
        return current_user
        
    return permission_checker
