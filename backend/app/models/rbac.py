from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Many-to-many relationship for Role <-> Permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)

class Permission(Base):
    """
    Represents an atomic permission or scope. e.g. "users:read", "memberships:write".
    Permissions are global system definitions.
    """
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    
    roles: Mapped[list["Role"]] = relationship("Role", secondary=role_permissions, back_populates="permissions")

class Role(Base):
    """
    Represents a role which contains multiple permissions.
    These could be system-defined roles or custom roles.
    """
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)

    permissions: Mapped[list["Permission"]] = relationship("Permission", secondary=role_permissions, back_populates="roles")
    user_roles: Mapped[list["UserRole"]] = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

class UserRole(Base):
    """
    Associates a user with a role within the context of a specific tenant, federation (organization), or globally.
    """
    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)

    __table_args__ = (
        # Ensure a role assignment is scoped to EITHER a tenant, OR an organization, OR neither (global), but NOT both.
        # This prevents ambiguity in role scoping.
        sa.CheckConstraint(
            "(tenant_id IS NULL) OR (organization_id IS NULL)",
            name="chk_user_roles_tenant_or_org"
        ),
    )

    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
