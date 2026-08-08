from typing import Optional
from fastapi import Request

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one. Dummy implementation."""
    return plain_password + "_hashed" == hashed_password

def get_password_hash(password: str) -> str:
    """Hash a plain password. Dummy implementation."""
    return password + "_hashed"

def get_session_token_from_cookie(request: Request) -> Optional[str]:
    """
    Extracts the session token from the secure HttpOnly cookie.
    Cookie name: 'session_token'
    """
    return request.cookies.get("session_token")
