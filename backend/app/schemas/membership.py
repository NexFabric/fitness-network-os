from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MembershipFreezeCreate(BaseModel):
    start_date: datetime
    expected_end_date: datetime | None = None
    reason: str | None = None


class MembershipFreezeResponse(BaseModel):
    id: UUID
    membership_id: UUID
    start_date: datetime
    expected_end_date: datetime | None = None
    actual_end_date: datetime | None = None
    reason: str | None = None
    tenant_id: UUID

    model_config = ConfigDict(from_attributes=True)

class MembershipResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    member_id: UUID
    plan_version_id: UUID
    status: str
    start_date: datetime
    end_date: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class MembershipCancellationCreate(BaseModel):
    effective_date: datetime
    reason: str | None = None

class MembershipCancellationResponse(BaseModel):
    id: UUID
    membership_id: UUID
    cancelled_at: datetime
    effective_date: datetime
    reason: str | None = None
    tenant_id: UUID

    model_config = ConfigDict(from_attributes=True)

class MembershipRenewalCreate(BaseModel):
    next_plan_version_id: UUID
    renewal_date: datetime

class MembershipRenewalResponse(BaseModel):
    id: UUID
    membership_id: UUID
    next_plan_version_id: UUID | None = None
    renewal_date: datetime
    price_snapshot: int | None = None
    terms_snapshot: str | None = None
    tenant_id: UUID

    model_config = ConfigDict(from_attributes=True)
