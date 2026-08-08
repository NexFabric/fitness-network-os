from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, JSON, Integer, DateTime
from typing import Any, Dict, Optional
from datetime import datetime

from app.db.base import Base, TenantMixin

class IdempotencyKey(Base, TenantMixin):
    """
    Prevents double execution for critical POST/action operations.
    As per ADR-036.
    """
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    request_path: Mapped[str] = mapped_column(String(255), nullable=False)
    request_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
