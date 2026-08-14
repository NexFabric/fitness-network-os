import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, TenantMixin


class OnboardingStage(str, enum.Enum):
    ORG_CREATED = "ORG_CREATED"
    TENANT_CONFIGURED = "TENANT_CONFIGURED"
    LOCATION_CREATED = "LOCATION_CREATED"
    PLANS_DEFINED = "PLANS_DEFINED"
    STAFF_INVITED = "STAFF_INVITED"
    COMPLETED = "COMPLETED"


class TenantOnboarding(TenantMixin, Base):
    __tablename__ = "tenant_onboardings"

    current_stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=OnboardingStage.ORG_CREATED.value,
    )
    step_data: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
        server_default="{}",
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
