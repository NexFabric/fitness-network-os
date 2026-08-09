"""Phase 14 staff linking — User ≠ Member; staff links User to tenant (flush-only)."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.staff import Staff
from app.models.user import User

ALLOWED_STAFF_ROLES = frozenset(
    {"STAFF", "TRAINER", "FRONT_DESK", "MANAGER", "ADMIN"}
)


class StaffService:
    def __init__(self, db: AsyncSession):
        self.db = db

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
