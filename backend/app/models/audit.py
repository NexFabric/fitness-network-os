from typing import Any
from uuid import UUID

from sqlalchemy import JSON, String, Uuid, event
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class AuditEvent(Base, TenantMixin):
    """
    Strictly immutable audit log for critical actions.
    No UPDATE or DELETE operations should be allowed on this table.
    """

    __tablename__ = "audit_events"

    user_id: Mapped[UUID | None] = mapped_column(Uuid, index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(Uuid, index=True, nullable=True)

    # Store old and new states for auditing changes
    old_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    new_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)


@event.listens_for(AuditEvent, "before_update")
def receive_before_update(mapper, connection, target):
    raise Exception("Audit events are strictly immutable and cannot be updated.")


@event.listens_for(AuditEvent, "before_delete")
def receive_before_delete(mapper, connection, target):
    raise Exception("Audit events are strictly immutable and cannot be deleted.")
