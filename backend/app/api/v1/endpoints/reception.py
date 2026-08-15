"""Front Desk Reception Workspace endpoints for GymClubNex."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService
from app.models.access import AccessAttempt, AccessStatus, Checkin
from app.models.entitlement import EntitlementWallet
from app.models.finance import BillingAccount, Invoice, Payment
from app.models.location import Location
from app.models.member import Member, Note, Tag
from app.models.membership import Membership
from app.models.user import User

router = APIRouter()


class ReceptionMemberSearchResult(BaseModel):
    id: UUID
    member_number: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    status: str
    has_active_membership: bool
    total_remaining_entitlements: int

    model_config = ConfigDict(from_attributes=True)


class ReceptionMemberDetailResponse(BaseModel):
    id: UUID
    member_number: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    status: str
    tags: list[str]
    notes: list[str]
    memberships: list[dict]
    wallets: list[dict]
    invoices: list[dict]
    payments: list[dict]
    recent_checkins: list[dict]
    total_debt_minor: int
    currency: str = "TRY"

    model_config = ConfigDict(from_attributes=True)


class ManualCheckinOverrideRequest(BaseModel):
    location_id: UUID
    reason: Annotated[str, Field(min_length=3, max_length=255)]
    device_id: UUID | None = None


class ManualCheckinOverrideResponse(BaseModel):
    checkin_id: UUID
    member_id: UUID
    location_id: UUID
    checkin_time: datetime
    message: str


@router.get("/search", response_model=list[ReceptionMemberSearchResult])
async def search_members_for_reception(
    q: Annotated[str, Query(min_length=1, max_length=100)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Instant multi-field search for reception staff."""
    AuthorizationService.require_tenant(current_user, "members:read", tenant_id)

    search_term = f"%{q}%"
    stmt = (
        select(Member)
        .where(
            Member.tenant_id == tenant_id,
            or_(
                Member.first_name.ilike(search_term),
                Member.last_name.ilike(search_term),
                Member.member_number.ilike(search_term),
                Member.email.ilike(search_term),
                Member.phone.ilike(search_term),
            ),
        )
        .limit(20)
    )
    members = list((await db.execute(stmt)).scalars().all())

    results: list[ReceptionMemberSearchResult] = []
    for m in members:
        # Check active membership
        res_act = await db.execute(
            select(Membership.id).where(
                Membership.tenant_id == tenant_id,
                Membership.member_id == m.id,
                Membership.status == "ACTIVE",
            )
        )
        has_active = res_act.first() is not None

        # Check remaining entitlements
        res_wallets = await db.execute(
            select(EntitlementWallet).where(
                EntitlementWallet.tenant_id == tenant_id,
                EntitlementWallet.member_id == m.id,
            )
        )
        wallets = list(res_wallets.scalars().all())
        total_remaining = sum(w.remaining for w in wallets)

        results.append(
            ReceptionMemberSearchResult(
                id=m.id,
                member_number=m.member_number,
                first_name=m.first_name,
                last_name=m.last_name,
                email=m.email,
                phone=m.phone,
                status=m.status,
                has_active_membership=has_active,
                total_remaining_entitlements=total_remaining,
            )
        )

    return results


@router.get("/member/{member_id}", response_model=ReceptionMemberDetailResponse)
async def get_reception_member_detail(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Detailed member profile card for front-desk reception."""
    AuthorizationService.require_tenant(current_user, "members:read", tenant_id)

    member = await db.get(Member, member_id)
    if member is None or member.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Üye bulunamadı.",
        )

    # Tags & Notes
    tags_res = await db.execute(
        select(Tag.name).where(Tag.tenant_id == tenant_id, Tag.member_id == member_id)
    )
    tags = list(tags_res.scalars().all())

    notes_res = await db.execute(
        select(Note.content).where(
            Note.tenant_id == tenant_id, Note.member_id == member_id
        )
    )
    notes = list(notes_res.scalars().all())

    # Memberships
    m_res = await db.execute(
        select(Membership)
        .where(Membership.tenant_id == tenant_id, Membership.member_id == member_id)
        .order_by(Membership.created_at.desc())
    )
    memberships = [
        {
            "id": str(m.id),
            "status": m.status,
            "start_date": m.start_date.isoformat() if m.start_date else None,
            "end_date": m.end_date.isoformat() if m.end_date else None,
        }
        for m in m_res.scalars().all()
    ]

    # Entitlement Wallets
    w_res = await db.execute(
        select(EntitlementWallet).where(
            EntitlementWallet.tenant_id == tenant_id,
            EntitlementWallet.member_id == member_id,
        )
    )
    wallets = [
        {
            "id": str(w.id),
            "entitlement_id": str(w.entitlement_id),
            "allocated": w.allocated,
            "remaining": w.remaining,
            "expires_at": w.expires_at.isoformat() if w.expires_at else None,
        }
        for w in w_res.scalars().all()
    ]

    # Invoices & Debt
    inv_res = await db.execute(
        select(Invoice)
        .join(BillingAccount, Invoice.billing_account_id == BillingAccount.id)
        .where(
            Invoice.tenant_id == tenant_id,
            BillingAccount.member_id == member_id,
        )
        .order_by(Invoice.created_at.desc())
    )
    invoices_list = list(inv_res.scalars().all())
    invoices = [
        {
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "status": inv.status,
            "total_amount_minor": inv.total_amount_minor,
            "paid_amount_minor": inv.paid_amount_minor,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        }
        for inv in invoices_list
    ]

    total_debt = sum(
        (inv.total_amount_minor - inv.paid_amount_minor)
        for inv in invoices_list
        if inv.status in ("OPEN", "PARTIALLY_PAID")
    )

    # Payments
    pay_res = await db.execute(
        select(Payment)
        .join(BillingAccount, Payment.billing_account_id == BillingAccount.id)
        .where(
            Payment.tenant_id == tenant_id,
            BillingAccount.member_id == member_id,
        )
        .order_by(Payment.created_at.desc())
        .limit(10)
    )
    payments = [
        {
            "id": str(p.id),
            "amount_minor": p.amount_minor,
            "currency": p.currency,
            "status": p.status,
            "method": p.method,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in pay_res.scalars().all()
    ]

    # Recent Checkins
    chk_res = await db.execute(
        select(Checkin)
        .where(Checkin.tenant_id == tenant_id, Checkin.member_id == member_id)
        .order_by(Checkin.checkin_time.desc())
        .limit(5)
    )
    recent_checkins = [
        {
            "id": str(c.id),
            "location_id": str(c.location_id),
            "checkin_time": c.checkin_time.isoformat() if c.checkin_time else None,
            "checkout_time": c.checkout_time.isoformat() if c.checkout_time else None,
        }
        for c in chk_res.scalars().all()
    ]

    return ReceptionMemberDetailResponse(
        id=member.id,
        member_number=member.member_number,
        first_name=member.first_name,
        last_name=member.last_name,
        email=member.email,
        phone=member.phone,
        status=member.status,
        tags=tags,
        notes=notes,
        memberships=memberships,
        wallets=wallets,
        invoices=invoices,
        payments=payments,
        recent_checkins=recent_checkins,
        total_debt_minor=total_debt,
        currency="TRY",
    )


@router.post(
    "/checkin/{member_id}/override",
    response_model=ManualCheckinOverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def manual_checkin_override(
    member_id: UUID,
    body: ManualCheckinOverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Manual turnstile/access override performed by front desk staff."""
    AuthorizationService.require_tenant(current_user, "access:override", tenant_id)

    member = await db.get(Member, member_id)
    if member is None or member.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Üye bulunamadı.",
        )

    location = await db.get(Location, body.location_id)
    if location is None or location.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lokasyon bulunamadı.",
        )

    now = datetime.now(UTC)

    # 1. Create Checkin
    checkin = Checkin(
        tenant_id=tenant_id,
        member_id=member_id,
        location_id=body.location_id,
        device_id=body.device_id,
        checkin_time=now,
    )
    db.add(checkin)
    await db.flush()

    # 2. Record Forensic Attempt Snapshot
    attempt = AccessAttempt(
        tenant_id=tenant_id,
        member_id=member_id,
        device_id=body.device_id,
        status=AccessStatus.GRANTED,
        denial_reason=None,
        jti=f"override-{checkin.id}",
        method="MANUAL_OVERRIDE",
        snapshot_data={
            "staff_user_id": str(current_user.id),
            "override_reason": body.reason,
            "checkin_id": str(checkin.id),
            "location_id": str(body.location_id),
            "device_id": str(body.device_id) if body.device_id else None,
            "timestamp": now.isoformat(),
        },
        timestamp=now,
    )
    db.add(attempt)

    # 3. Create Immutable Audit Event
    from app.models.audit import AuditEvent

    audit_event = AuditEvent(
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="access.manual_override",
        resource_type="member",
        resource_id=member_id,
        new_state={
            "override_reason": body.reason,
            "checkin_id": str(checkin.id),
            "location_id": str(body.location_id),
            "device_id": str(body.device_id) if body.device_id else None,
        },
    )
    db.add(audit_event)

    await db.commit()
    await db.refresh(checkin)

    return ManualCheckinOverrideResponse(
        checkin_id=checkin.id,
        member_id=member_id,
        location_id=body.location_id,
        checkin_time=checkin.checkin_time,
        message="Manuel giriş başarıyla onaylandı ve kaydedildi.",
    )
