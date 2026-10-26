"""A user holds a given role at most once per tenant / org / global scope."""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.organization import Organization
from app.models.rbac import Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User


@pytest.mark.asyncio
async def test_duplicate_tenant_role_grant_is_rejected(pg_engine):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="UR Org", domain=f"ur-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="UR Tenant",
            organization_id=org.id,
            location_code=f"UR-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        user = User(
            email=f"ur-{uuid4().hex[:8]}@example.com",
            hashed_password="x",
            is_active=True,
        )
        db.add(user)
        role = Role(
            name=f"UR-{uuid4().hex[:8]}", description="unique grant", is_system=False
        )
        db.add(role)
        await db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id))
        await db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id, tenant_id=tenant.id))
        with pytest.raises(IntegrityError):
            await db.flush()
        await db.rollback()
