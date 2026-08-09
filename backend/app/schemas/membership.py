from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MembershipFreezeCreate(BaseModel):
    start_date: datetime
    expected_end_date: datetime
    reason: Optional[str] = None


class MembershipFreezeResponse(BaseModel):
    id: UUID
    membership_id: UUID
    start_date: datetime
    expected_end_date: datetime
    actual_end_date: Optional[datetime] = None
    reason: Optional[str] = None
    tenant_id: UUID

    class Config:
        from_attributes = True

class MembershipResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    member_id: UUID
    plan_version_id: UUID
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True
