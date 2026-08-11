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

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


async def get_current_user(
    token: str = Depends(get_current_session_token), db: AsyncSession = Depends(get_db)
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
            UserSession.expires_at > datetime.now(UTC),
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


async def _audit_superuser_tenant_access(
    db: AsyncSession, user: User, tenant_id: UUID
) -> None:
    """Record a superuser asserting a tenant it holds no UserRole for.

    ``is_superuser`` lets a caller name any tenant in X-Tenant-ID. That is a
    deliberate operational capability, but it used to leave no trace and was
    indistinguishable from ordinary tenant traffic in the logs.
    """
    from app.models.audit import AuditEvent

    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id, UserRole.tenant_id == tenant_id
        )
    )
    if result.scalars().first() is not None:
        # Genuine member of the tenant — not impersonation.
        return

    db.add(
        AuditEvent(
            tenant_id=tenant_id,
            user_id=user.id,
            action="superuser.tenant_impersonation",
            resource_type="tenant",
            resource_id=tenant_id,
            new_state={"email": user.email},
        )
    )
    await db.flush()


async def get_tenant_id(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """Dependency to extract and validate the X-Tenant-ID header."""
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid X-Tenant-ID header format. Must be a UUID."
        )

    if user.is_superuser:
        current_tenant_id_var.set(tenant_id)
        await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}';"))
        await _audit_superuser_tenant_access(db, user, tenant_id)
        return tenant_id

    # Temporarily set the RLS context so we can read the UserRole for this tenant
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}';"))

    # Verify user belongs to the requested tenant via UserRole
    result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id, UserRole.tenant_id == tenant_id
        )
    )
    user_role = result.scalars().first()

    if not user_role:
        # Reset RLS if unauthorized
        await db.execute(text("SET LOCAL app.current_tenant_id = '';"))
        raise HTTPException(
            status_code=403, detail="User does not have access to this tenant"
        )

    current_tenant_id_var.set(tenant_id)
    return tenant_id


class FederationScope:
    """Which organizations a federation-level caller may read across.

    ``org_ids is None`` means platform scope (every organization). A list means
    exactly those organizations; an empty list means nothing is readable.
    """

    def __init__(self, user: User, org_ids: list[UUID] | None):
        self.user = user
        self.org_ids = org_ids

    @property
    def is_platform(self) -> bool:
        return self.org_ids is None


FEDERATION_ROLE_NAMES = {
    "FEDERATION_ADMIN",
    "FEDERATION_ANALYST",
    "FEDERATION_SUPPORT",
}


async def get_federation_scope(
    user: User = Depends(get_current_user),
) -> FederationScope:
    """Authorize a cross-tenant read and derive its organization scope.

    Deliberately does not depend on ``get_tenant_id``: federation reads address
    no single tenant, so requiring X-Tenant-ID would be meaningless. Scope comes
    from the caller's own role assignments, never from a client-supplied value.
    """
    if user.is_superuser:
        return FederationScope(user, None)

    org_ids: list[UUID] = []
    for user_role in user.user_roles:
        role = user_role.role
        if role is None:
            continue
        if (
            user_role.tenant_id is None
            and user_role.organization_id is None
            and role.name == "PLATFORM_SUPER_ADMIN"
        ):
            return FederationScope(user, None)
        if user_role.organization_id is not None and role.name in FEDERATION_ROLE_NAMES:
            org_ids.append(user_role.organization_id)

    if not org_ids:
        raise HTTPException(
            status_code=403, detail="Not a platform or federation principal"
        )
    return FederationScope(user, org_ids)


async def get_current_device(request: Request, db: AsyncSession = Depends(get_db)):
    import hashlib

    from app.models.access import Device, DeviceSession, DeviceStatus

    token = request.cookies.get("device_session")
    auth_header = request.headers.get("Authorization")
    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated as device")

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    from datetime import datetime

    result = await db.execute(
        select(DeviceSession).where(
            DeviceSession.token_hash == token_hash,
            DeviceSession.is_revoked == False,
            DeviceSession.expires_at > datetime.now(UTC),
        )
    )
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired device session")

    result_device = await db.execute(
        select(Device).where(Device.id == session.device_id)
    )
    device = result_device.scalars().first()

    if not device or not device.is_active or device.status == DeviceStatus.OFFLINE:
        # If device was marked offline by revocation or something else
        raise HTTPException(status_code=401, detail="Device inactive or offline")

    current_tenant_id_var.set(device.tenant_id)
    await db.execute(text(f"SET LOCAL app.current_tenant_id = '{device.tenant_id}';"))
    return device
