"""Row-level scoping for member reads.

``members:read`` decides whether a caller may call a member endpoint at all;
``members:read:all`` decides whether it sees the whole tenant. A caller with the
first but not the second (today: TRAINER) is restricted to the members assigned
to it in ``trainer_assignments``.

Keeping the row scope here — rather than in the permission name checked by each
handler — means there is exactly one place that answers "which members?", and
handlers cannot forget it by using the wrong permission string.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.trainer_assignment import TrainerAssignmentService

READ_ALL_PERMISSION = "members:read:all"


def has_tenant_wide_member_read(user: User, tenant_id: UUID) -> bool:
    return AuthorizationService.is_authorized(
        user=user,
        permission=READ_ALL_PERMISSION,
        resource_tenant_id=tenant_id,
    )


async def visible_member_ids(
    db: AsyncSession, user: User, tenant_id: UUID
) -> list[UUID] | None:
    """Member ids the caller may see, or ``None`` when unrestricted.

    ``None`` means "no row filter" — not "no members". An empty list means the
    caller is assignment-scoped and currently has no assignments.
    """
    if has_tenant_wide_member_read(user, tenant_id):
        return None
    return await TrainerAssignmentService(db).assigned_member_ids(tenant_id, user.id)


async def require_member_visible(
    db: AsyncSession, user: User, tenant_id: UUID, member_id: UUID
) -> None:
    """Raise SecurityException unless the caller may see this specific member."""
    if has_tenant_wide_member_read(user, tenant_id):
        return
    assigned = await TrainerAssignmentService(db).is_assigned(
        tenant_id, user.id, member_id
    )
    if not assigned:
        raise SecurityException("member not assigned to caller")
