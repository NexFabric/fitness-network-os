from fastapi import Header, HTTPException, Request, status
from typing import Optional

async def verify_idempotency_key(
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> Optional[str]:
    """
    Dependency that enforces the presence and validation of Idempotency-Key 
    for critical state-changing endpoints (e.g. POST, PUT, PATCH).
    
    If the key is provided:
    In a real implementation, this would check if the key already exists
    in the database (idempotency_keys table). If it does and it hasn't expired,
    it would immediately return the cached response (or raise an error if 
    processing is still ongoing).
    """
    # For GET/OPTIONS/HEAD methods, idempotency isn't usually required
    if request.method in ["GET", "OPTIONS", "HEAD"]:
        return None

    # We might only enforce this on specific sensitive routes, 
    # but when this dependency is applied, we enforce the header.
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Idempotency-Key header is required for this operation."
        )

    # TODO: Query IdempotencyKey model to check for existence and return cached response if needed.

    return idempotency_key
