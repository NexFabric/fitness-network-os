from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    devices: Mapped[List["UserDevice"]] = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    mfa_methods: Mapped[List["UserMfaMethod"]] = relationship("UserMfaMethod", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "user_sessions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    user: Mapped["User"] = relationship("User", back_populates="sessions")

class UserDevice(Base):
    __tablename__ = "user_devices"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False) # e.g. FCM token or hardware UUID
    device_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    user: Mapped["User"] = relationship("User", back_populates="devices")

class UserMfaMethod(Base):
    __tablename__ = "user_mfa_methods"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    method_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. 'totp', 'sms'
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    user: Mapped["User"] = relationship("User", back_populates="mfa_methods")
