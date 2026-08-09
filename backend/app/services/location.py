"""Phase 14 location / branch core (flush-only)."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location


class LocationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_location(
        self,
        tenant_id: UUID,
        *,
        name: str,
        timezone: str = "UTC",
        address: str | None = None,
    ) -> Location:
        name = name.strip()
        if not name:
            raise ValueError("location_name_required")
        loc = Location(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            timezone=timezone or "UTC",
            address=address,
        )
        self.db.add(loc)
        await self.db.flush()
        return loc

    async def get_location(self, tenant_id: UUID, location_id: UUID) -> Location | None:
        result = await self.db.execute(
            select(Location).where(
                Location.tenant_id == tenant_id, Location.id == location_id
            )
        )
        return result.scalars().first()

    async def list_locations(self, tenant_id: UUID) -> list[Location]:
        result = await self.db.execute(
            select(Location)
            .where(Location.tenant_id == tenant_id)
            .order_by(Location.name)
        )
        return list(result.scalars().all())

    async def update_location(
        self,
        tenant_id: UUID,
        location_id: UUID,
        *,
        name: str | None = None,
        timezone: str | None = None,
        address: str | None = None,
    ) -> Location:
        loc = await self.get_location(tenant_id, location_id)
        if loc is None:
            raise ValueError("location_not_found")
        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("location_name_required")
            loc.name = name
        if timezone is not None:
            loc.timezone = timezone
        if address is not None:
            loc.address = address
        await self.db.flush()
        return loc
