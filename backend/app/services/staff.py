"""Phase 14 staff linking — User ≠ Member; staff links User to tenant (flush-only)."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.location import Location
from app.models.rbac import Role, UserRole
from app.models.staff import Staff
from app.models.user import User

# Who may appear as class_sessions.trainer_user_id / schedules.
# PT bookings are narrower: TRAINER only (see has_tenant_role(..., pt_only)).
CLASS_TRAINER_ROLES = frozenset({"TRAINER", "GYM_OWNER", "GYM_ADMIN", "GYM_MANAGER"})
PT_TRAINER_ROLES = frozenset({"TRAINER"})

ALLOWED_STAFF_ROLES = frozenset(
    {
        "STAFF",
        "TRAINER",
        "FRONT_DESK",
        "MANAGER",
        "ADMIN",
        "GYM_ADMIN",
        "GYM_MANAGER",
        "ACCOUNTANT",
    }
)

# Staff.role is a job label; login permissions come from the canonical RBAC
# role. GYM_OWNER and platform roles are intentionally absent.
STAFF_ROLE_TO_RBAC = {
    "STAFF": "FRONT_DESK",
    "TRAINER": "TRAINER",
    "FRONT_DESK": "FRONT_DESK",
    "MANAGER": "GYM_MANAGER",
    "ADMIN": "GYM_ADMIN",
    "GYM_ADMIN": "GYM_ADMIN",
    "GYM_MANAGER": "GYM_MANAGER",
    "ACCOUNTANT": "ACCOUNTANT",
}

# 20 URL-safe characters ≈ 119 bits of entropy. Shown once to the administrator
# who provisioned the account and never stored in the clear.
_ONE_TIME_PASSWORD_BYTES = 15


def generate_one_time_password() -> str:
    return secrets.token_urlsafe(_ONE_TIME_PASSWORD_BYTES)


@dataclass
class ProvisionedStaff:
    staff: Staff
    user: User
    one_time_password: str


class StaffService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_staff_account(
        self,
        tenant_id: UUID,
        *,
        email: str,
        role: str = "STAFF",
        location_id: UUID | None = None,
    ) -> ProvisionedStaff:
        """Create a login for a new colleague and link it to this tenant.

        The account is provisioned with a one-time password and flagged for
        rotation, so the generated secret cannot become a standing credential.
        An address that already has an account is a conflict, not a silent
        rebind — quietly attaching someone else's login to your tenant would be
        a tenant-boundary problem, and the caller should link it deliberately.
        """
        normalized = email.strip().lower()
        if not normalized:
            raise ValueError("email_required")
        if role not in ALLOWED_STAFF_ROLES:
            raise ValueError(f"invalid_staff_role:{role}")

        # Validate everything that can fail *before* inserting the user, so a
        # rejected request never depends on rollback to avoid an orphaned login.
        if location_id is not None:
            loc = await self.db.execute(
                select(Location).where(
                    Location.tenant_id == tenant_id, Location.id == location_id
                )
            )
            if loc.scalars().first() is None:
                raise ValueError("location_not_found")

        existing = await self.db.execute(select(User).where(User.email == normalized))
        if existing.scalars().first() is not None:
            raise ValueError("email_already_registered")

        one_time_password = generate_one_time_password()
        user = User(
            id=uuid4(),
            email=normalized,
            hashed_password=get_password_hash(one_time_password),
            is_active=True,
            is_superuser=False,
            must_change_password=True,
        )
        self.db.add(user)
        try:
            await self.db.flush()
        except IntegrityError as e:
            # Lost a race against a concurrent create for the same address.
            raise ValueError("email_already_registered") from e

        staff = await self.link_staff(
            tenant_id, user_id=user.id, role=role, location_id=location_id
        )
        await self._attach_rbac_role(tenant_id, user.id, role)
        return ProvisionedStaff(
            staff=staff, user=user, one_time_password=one_time_password
        )

    async def _attach_rbac_role(
        self, tenant_id: UUID, user_id: UUID, staff_role: str
    ) -> None:
        rbac_name = STAFF_ROLE_TO_RBAC[staff_role]
        role = (
            await self.db.execute(select(Role).where(Role.name == rbac_name))
        ).scalar_one_or_none()
        if role is None:
            # Production always has the canonical row (permissions.yml seed).
            # Tests truncate `roles` between cases; recreate the named role so
            # the login principal is still bound. Grants are re-seeded by
            # Alembic on a real migrate, not here.
            role = Role(name=rbac_name, description=rbac_name, is_system=True)
            self.db.add(role)
            await self.db.flush()
        existing = (
            await self.db.execute(
                select(UserRole).where(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role.id,
                    UserRole.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return
        self.db.add(UserRole(user_id=user_id, role_id=role.id, tenant_id=tenant_id))
        await self.db.flush()

    async def link_staff(
        self,
        tenant_id: UUID,
        *,
        user_id: UUID,
        role: str = "STAFF",
        location_id: UUID | None = None,
    ) -> Staff:
        if role not in ALLOWED_STAFF_ROLES:
            raise ValueError(f"invalid_staff_role:{role}")

        user = await self.db.get(User, user_id)
        if user is None:
            raise ValueError("user_not_found")

        if location_id is not None:
            loc = await self.db.execute(
                select(Location).where(
                    Location.tenant_id == tenant_id, Location.id == location_id
                )
            )
            if loc.scalars().first() is None:
                raise ValueError("location_not_found")

        existing = await self.db.execute(
            select(Staff).where(Staff.tenant_id == tenant_id, Staff.user_id == user_id)
        )
        staff = existing.scalars().first()
        if staff:
            staff.role = role
            staff.location_id = location_id
            await self.db.flush()
            await self._attach_rbac_role(tenant_id, user_id, role)
            return staff

        staff = Staff(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            location_id=location_id,
        )
        self.db.add(staff)
        try:
            await self.db.flush()
        except IntegrityError as e:
            raise ValueError("staff_link_conflict") from e
        await self._attach_rbac_role(tenant_id, user_id, role)
        return staff

    async def list_staff(self, tenant_id: UUID) -> list[Staff]:
        result = await self.db.execute(
            select(Staff).where(Staff.tenant_id == tenant_id).order_by(Staff.created_at)
        )
        return list(result.scalars().all())

    async def list_staff_with_emails(
        self, tenant_id: UUID
    ) -> list[tuple[Staff, str | None]]:
        result = await self.db.execute(
            select(Staff, User.email)
            .outerjoin(User, User.id == Staff.user_id)
            .where(Staff.tenant_id == tenant_id)
            .order_by(Staff.created_at)
        )
        return [(row[0], row[1]) for row in result.all()]

    @staticmethod
    async def has_tenant_role(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        role_names: frozenset[str],
    ) -> bool:
        """True if ``user_id`` holds one of ``role_names`` in this tenant.

        ``users`` is global; ``user_roles.tenant_id`` is the mapping that
        keeps trainer_user_id from pointing at another gym's login.
        """
        from app.models.rbac import Role, UserRole

        found = (
            await db.execute(
                select(UserRole.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(
                    UserRole.tenant_id == tenant_id,
                    UserRole.user_id == user_id,
                    Role.name.in_(role_names),
                )
                .limit(1)
            )
        ).first()
        return found is not None

    @staticmethod
    async def is_employed(db: AsyncSession, tenant_id: UUID, user_id: UUID) -> bool:
        found = (
            await db.execute(
                select(Staff.id).where(
                    Staff.tenant_id == tenant_id, Staff.user_id == user_id
                )
            )
        ).first()
        return found is not None

    async def list_trainers(self, tenant_id: UUID) -> list[tuple[UUID, str]]:
        """Active employed trainers: UserRole.TRAINER ∩ staff ∩ is_active."""
        from app.models.rbac import Role, UserRole

        result = await self.db.execute(
            select(User.id, User.email)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .join(
                Staff,
                (Staff.tenant_id == UserRole.tenant_id) & (Staff.user_id == User.id),
            )
            .where(
                UserRole.tenant_id == tenant_id,
                Role.name == "TRAINER",
                User.is_active.is_(True),
            )
            .order_by(User.email)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def get_staff(self, tenant_id: UUID, staff_id: UUID) -> Staff | None:
        result = await self.db.execute(
            select(Staff).where(Staff.tenant_id == tenant_id, Staff.id == staff_id)
        )
        return result.scalars().first()

    async def get_user_email(self, user_id: UUID) -> str | None:
        user = await self.db.get(User, user_id)
        return user.email if user is not None else None
