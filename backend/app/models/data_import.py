import enum
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TenantMixin


class ImportBatchStatus(str, enum.Enum):
    PREVIEW = "PREVIEW"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ImportRowStatus(str, enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    IMPORTED = "IMPORTED"
    FAILED = "FAILED"


class DataImportBatch(TenantMixin, Base):
    __tablename__ = "data_import_batches"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ImportBatchStatus.PREVIEW.value,
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by_user_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    rows: Mapped[list["DataImportRow"]] = relationship(
        "DataImportRow",
        back_populates="batch",
        cascade="all, delete-orphan",
    )

    _model_table_args = (
        UniqueConstraint("tenant_id", "id", name="uq_data_import_batches_tenant_id_id"),
    )


class DataImportRow(TenantMixin, Base):
    __tablename__ = "data_import_rows"

    batch_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ImportRowStatus.VALID.value,
    )
    raw_data: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=False,
    )
    parsed_data: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    _model_table_args = (
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["data_import_batches.tenant_id", "data_import_batches.id"],
        ),
    )

    batch: Mapped["DataImportBatch"] = relationship(
        "DataImportBatch",
        back_populates="rows",
    )
