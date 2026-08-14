import enum

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class DeletionMethod(str, enum.Enum):
    DELETE = "DELETE"
    ANONYMIZE = "ANONYMIZE"
    ARCHIVE = "ARCHIVE"


class DataRetentionPolicy(TenantMixin, Base):
    """Retention policy per data category per tenant.

    Actual retention_days values are BUSINESS/LEGAL decisions,
    not engineering defaults. The system stores the policy;
    enforcement is via scheduled jobs (future implementation).
    """

    __tablename__ = "data_retention_policies"

    data_category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    retention_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="NULL = indefinite retention (requires legal basis)",
    )
    deletion_method: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DeletionMethod.ANONYMIZE.value
    )
    legal_basis: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_legal_review: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="True = retention_days must be set by legal/business, not engineering",
    )

    _model_table_args = (
        UniqueConstraint(
            "tenant_id",
            "data_category",
            name="uq_data_retention_policies_tenant_category",
        ),
        CheckConstraint(
            "deletion_method IN ('DELETE', 'ANONYMIZE', 'ARCHIVE')",
            name="ck_retention_policies_deletion_method",
        ),
        CheckConstraint(
            "retention_days IS NULL OR retention_days > 0",
            name="ck_retention_policies_days_positive",
        ),
    )
