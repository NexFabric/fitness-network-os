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
from app.models.staff import Staff
from app.models.user import User

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
        return ProvisionedStaff(
            staff=staff, user=user, one_time_password=one_time_password
        )

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
        return staff

    async def list_staff(self, tenant_id: UUID) -> list[Staff]:
        result = await self.db.execute(
            select(Staff).where(Staff.tenant_id == tenant_id).order_by(Staff.created_at)
        )
        return list(result.scalars().all())

    async def get_staff(self, tenant_id: UUID, staff_id: UUID) -> Staff | None:
        result = await self.db.execute(
            select(Staff).where(Staff.tenant_id == tenant_id, Staff.id == staff_id)
        )
        return result.scalars().first()
