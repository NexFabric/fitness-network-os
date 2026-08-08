from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, ForeignKeyConstraint, Uuid
from typing import Optional
from uuid import UUID

from app.db.base import Base, TenantMixin

class NotificationTemplate(Base, TenantMixin):
    """
    Template for sending emails, SMS, or push notifications.
    """
    __tablename__ = "notification_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # EMAIL, SMS, PUSH
    subject_template: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)


class NotificationDelivery(Base, TenantMixin):
    """
    Tracks the delivery status of a notification to a user.
    """
    __tablename__ = "notification_deliveries"

    template_id: Mapped[Optional[UUID]] = mapped_column(Uuid, nullable=True)
    recipient_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "template_id"], ["notification_templates.tenant_id", "notification_templates.id"]),
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    template: Mapped[Optional["NotificationTemplate"]] = relationship("NotificationTemplate")
    recipient: Mapped["User"] = relationship("User")
