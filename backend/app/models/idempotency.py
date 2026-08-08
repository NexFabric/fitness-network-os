from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantMixin


class IdempotencyKey(Base, TenantMixin):
    """
    Prevents double execution for critical POST/action operations.
    As per ADR-036.
    """
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    request_path: Mapped[str] = mapped_column(String(255), nullable=False)
    request_params: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
