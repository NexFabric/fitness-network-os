"""Member self-service routes — never accept caller-controlled member_id.

Pattern matches POST /access/qr/issue-self (Phase 15.5B/C):
current_user.id → members.user_id binding → server-owned member_id.
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_db,
    get_optional_tenant_id,
    get_tenant_id,
)
from app.core.authorization import AuthorizationService, SecurityException
from app.models.access import Checkin
from app.models.consent import ConsentRecord
from app.models.finance import BillingAccount, Invoice, Payment
from app.models.user import User
from app.schemas.membership import MembershipResponse
from app.services.entitlement import EntitlementService
from app.services.member import MemberService
from app.services.membership import MembershipService

router = APIRouter()

StrictQty = Annotated[StrictInt, Field(ge=1)]


class MeEntitlementCheckRequest(BaseModel):
    action: str
    quantity: StrictQty = 1


class MeEntitlementAccessResponse(BaseModel):
    granted: bool
    last_known_state: str
    offline_ttl_hours: int | None = None
    reason: str | None = None
    remaining: int | None = None
    member_id: UUID


class MeMemberResponse(BaseModel):
    """Read-only member card for the bound login user (no staff-only fields)."""

    id: UUID
    tenant_id: UUID
    member_number: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    status: str
    user_id: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeProfileResponse(BaseModel):
    """Thin self profile: login user + bound member card (no client member_id)."""

    user_id: UUID
    email: str | None
    tenant_id: UUID
    member: MeMemberResponse


class MeSessionResponse(BaseModel):
    """Who-am-I for any authenticated principal — staff included.

    Distinct from ``/me/profile``, which 404s when no member row is bound and so
    can never answer this for staff. Roles/permissions are the ones effective in
    the requested tenant plus platform/federation-scoped grants.
    """

    user_id: UUID
    # null for federation/platform principals, which belong to no single tenant.
    tenant_id: UUID | None
    email: str | None
    is_superuser: bool
    roles: list[str]
    permissions: list[str]
    has_member_binding: bool


class MeWalletSummary(BaseModel):
    """Entitlement wallet row for the bound member (read-only snapshot)."""

    wallet_id: UUID
    membership_id: UUID
    entitlement_id: UUID
    entitlement_code: str | None = None
    entitlement_name: str | None = None
    allocated: int
    reserved: int
    consumed: int
    remaining: int
    expires_at: datetime | None = None


class MeEntitlementsSummaryResponse(BaseModel):
    member_id: UUID
    wallets: list[MeWalletSummary]


class MeCheckinResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    member_id: UUID
    location_id: UUID
    device_id: UUID | None = None
    checkin_time: datetime
    checkout_time: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MeInvoiceResponse(BaseModel):
    id: UUID
    invoice_number: str | None = None
    status: str
    total_amount_minor: int
    paid_amount_minor: int
    discount_amount_minor: int
    currency: str
    due_date: datetime | None = None
    issued_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MePaymentResponse(BaseModel):
    id: UUID
    amount_minor: int
    refunded_amount_minor: int = 0
    currency: str
    status: str
    method: str
    paid_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeConsentRecordResponse(BaseModel):
    id: UUID
    consent_type: str
    document_version: str
    status: str
    given_at: datetime | None = None
    withdrawn_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MeConsentRecordRequest(BaseModel):
    consent_type: str
    document_version: str = "v1.0"
    status: str = "GIVEN"


async def _bound_member_or_404(db: AsyncSession, tenant_id: UUID, user_id: UUID):
    member = await MemberService(db).get_member_by_user_id(tenant_id, user_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="member_not_bound",
        )
    return member


@router.get("/session", response_model=MeSessionResponse)
async def get_my_session(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID | None = Depends(get_optional_tenant_id),
):
    """Effective roles and permissions for the caller.

    X-Tenant-ID is optional: a federation or platform principal holds no
    tenant-scoped role, and requiring a tenant would leave it unable to answer
    even "who am I". When a tenant is supplied, membership has already been
    proven by the dependency.

    No permission gate — this returns only what the caller already holds, so
    there is nothing here to escalate with.
    """
    roles: set[str] = set()
    permissions: set[str] = set()

    for user_role in current_user.user_roles:
        role = user_role.role
        if role is None:
            continue
        # Tenant-scoped grants count only for the tenant being addressed;
        # platform (both None) and federation (organization_id) grants are not
        # tenant-bound and always apply.
        if user_role.tenant_id is not None and user_role.tenant_id != tenant_id:
            continue
        roles.add(role.name)
        for permission in role.permissions or []:
            permissions.add(permission.name)

    member = (
        await MemberService(db).get_member_by_user_id(tenant_id, current_user.id)
        if tenant_id is not None
        else None
    )

    return MeSessionResponse(
        user_id=current_user.id,
        email=current_user.email,
        tenant_id=tenant_id,
        is_superuser=current_user.is_superuser,
        roles=sorted(roles),
        permissions=sorted(permissions),
        has_member_binding=member is not None,
    )


@router.get("/profile", response_model=MeProfileResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Self profile: user id + bound member card.

    ``profile:read`` is not ``*:self`` (no profile:read:self seeded). Authorize
    carefully with tenant + resource_owner_id=current_user.id so ownership is
    always the caller. Member is resolved server-side only.
    """
    if not AuthorizationService.is_authorized(
        user=current_user,
        permission="profile:read",
        resource_tenant_id=tenant_id,
        resource_owner_id=current_user.id,
    ):
        raise SecurityException()
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    return MeProfileResponse(
        user_id=current_user.id,
        email=current_user.email,
        tenant_id=tenant_id,
        member=MeMemberResponse.model_validate(member),
    )


@router.get("/member", response_model=MeMemberResponse)
async def get_my_member(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Bound member profile (read-only card) for the caller.

    No ``members:read:self`` exists; gate with ``memberships:read:self``
    (MEMBER self-service matrix) + require_self ownership. Binding is always
    server-side via members.user_id (no client member_id).
    """
    AuthorizationService.require_self(
        current_user,
        "memberships:read:self",
        tenant_id,
        resource_owner_id=current_user.id,
    )
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    return MeMemberResponse.model_validate(member)


@router.get("/memberships", response_model=list[MembershipResponse])
async def list_my_memberships(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List memberships for the bound member only (no path/body member_id)."""
    AuthorizationService.require_self(
        current_user,
        "memberships:read:self",
        tenant_id,
        resource_owner_id=current_user.id,
    )
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    rows = await MembershipService(db).list_memberships_for_member(tenant_id, member.id)
    return rows


@router.get("/entitlements", response_model=MeEntitlementsSummaryResponse)
async def list_my_entitlements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Wallet snapshot for the bound member (read-only; no consume)."""
    AuthorizationService.require_self(
        current_user,
        "entitlements:read:self",
        tenant_id,
        resource_owner_id=current_user.id,
    )
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    wallets = await EntitlementService.list_wallets_for_member(db, tenant_id, member.id)
    return MeEntitlementsSummaryResponse(
        member_id=member.id,
        wallets=[
            MeWalletSummary(
                wallet_id=w["wallet_id"],
                membership_id=w["membership_id"],
                entitlement_id=w["entitlement_id"],
                entitlement_code=w.get("entitlement_code"),
                entitlement_name=w.get("entitlement_name"),
                allocated=w["allocated"],
                reserved=w["reserved"],
                consumed=w["consumed"],
                remaining=w["remaining"],
                expires_at=w.get("expires_at"),
            )
            for w in wallets
        ],
    )


@router.get("/checkins", response_model=list[MeCheckinResponse])
async def list_my_checkins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List check-ins for the bound member only (Checkin model exists)."""
    AuthorizationService.require_self(
        current_user,
        "checkins:read:self",
        tenant_id,
        resource_owner_id=current_user.id,
    )
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    result = await db.execute(
        select(Checkin)
        .where(
            Checkin.tenant_id == tenant_id,
            Checkin.member_id == member.id,
        )
        .order_by(Checkin.checkin_time.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


@router.post(
    "/entitlements/check",
    response_model=MeEntitlementAccessResponse,
)
async def check_my_entitlement(
    body: MeEntitlementCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Self entitlement check: entitlements:check:self only; no path member_id.

    Ownership is proven via current_user.id (bound member resolved server-side).
    """
    # resource_owner_id = caller user id — required for *:self grants
    AuthorizationService.require_self(
        current_user,
        "entitlements:check:self",
        tenant_id,
        resource_owner_id=current_user.id,
    )
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    result = await EntitlementService.check_access(
        db, tenant_id, member.id, body.action, body.quantity
    )
    return MeEntitlementAccessResponse(
        granted=result["granted"],
        last_known_state=result["last_known_state"],
        offline_ttl_hours=result.get("offline_ttl_hours"),
        reason=result.get("reason"),
        remaining=result.get("remaining"),
        member_id=member.id,
    )


@router.get("/invoices", response_model=list[MeInvoiceResponse])
async def list_my_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List invoices for the bound member's billing account."""
    AuthorizationService.require_self(
        current_user,
        "finance:read:self",
        tenant_id,
        resource_owner_id=current_user.id,
    )
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    result = await db.execute(
        select(Invoice)
        .join(BillingAccount, Invoice.billing_account_id == BillingAccount.id)
        .where(
            Invoice.tenant_id == tenant_id,
            BillingAccount.member_id == member.id,
        )
        .order_by(Invoice.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/payments", response_model=list[MePaymentResponse])
async def list_my_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List payments for the bound member's billing account."""
    AuthorizationService.require_self(
        current_user,
        "finance:read:self",
        tenant_id,
        resource_owner_id=current_user.id,
    )
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    result = await db.execute(
        select(Payment)
        .join(BillingAccount, Payment.billing_account_id == BillingAccount.id)
        .where(
            Payment.tenant_id == tenant_id,
            BillingAccount.member_id == member.id,
        )
        .order_by(Payment.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/consents", response_model=list[MeConsentRecordResponse])
async def list_my_consents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List consent records for the bound member."""
    if not AuthorizationService.is_authorized(
        user=current_user,
        permission="profile:read",
        resource_tenant_id=tenant_id,
        resource_owner_id=current_user.id,
    ):
        raise SecurityException()
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    result = await db.execute(
        select(ConsentRecord)
        .where(
            ConsentRecord.tenant_id == tenant_id,
            ConsentRecord.member_id == member.id,
        )
        .order_by(ConsentRecord.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/consents", response_model=MeConsentRecordResponse)
async def record_my_consent(
    body: MeConsentRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Record or withdraw a consent decision for the bound member."""
    if not AuthorizationService.is_authorized(
        user=current_user,
        permission="profile:write",
        resource_tenant_id=tenant_id,
        resource_owner_id=current_user.id,
    ):
        raise SecurityException()
    member = await _bound_member_or_404(db, tenant_id, current_user.id)
    now = datetime.now(UTC)
    given_at = now if body.status == "GIVEN" else None
    withdrawn_at = now if body.status == "WITHDRAWN" else None

    record = ConsentRecord(
        tenant_id=tenant_id,
        member_id=member.id,
        consent_type=body.consent_type,
        document_version=body.document_version,
        status=body.status,
        given_at=given_at,
        withdrawn_at=withdrawn_at,
        source="MEMBER_PORTAL",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
