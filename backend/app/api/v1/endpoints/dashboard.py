"""Operational KPI aggregation endpoint for GymClubNex dashboard."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService
from app.models.access import Checkin
from app.models.finance import Invoice, Payment
from app.models.member import Member
from app.models.membership import Membership
from app.models.user import User

router = APIRouter()


class DashboardKPIResponse(BaseModel):
    active_members_count: int
    expiring_memberships_count: int
    today_checkins_count: int
    past_due_invoices_count: int
    past_due_invoices_amount_minor: int
    month_collected_amount_minor: int
    total_outstanding_debt_minor: int
    currency: str = "TRY"

    model_config = ConfigDict(from_attributes=True)


@router.get("/kpis", response_model=DashboardKPIResponse)
async def get_dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Retrieve operational high-level KPIs calculated server-side in Postgres."""
    AuthorizationService.require_tenant(current_user, "gym:read", tenant_id)

    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    in_30_days = today_start + timedelta(days=30)
    month_start = today_start.replace(day=1)

    # 1. Active Members
    res_active_members = await db.execute(
        select(func.count(Member.id)).where(
            Member.tenant_id == tenant_id,
            Member.status == "ACTIVE",
        )
    )
    active_members_count = res_active_members.scalar_one() or 0

    # 2. Expiring Memberships within 30 days
    res_expiring = await db.execute(
        select(func.count(Membership.id)).where(
            Membership.tenant_id == tenant_id,
            Membership.status == "ACTIVE",
            Membership.end_date.is_not(None),
            Membership.end_date >= today_start,
            Membership.end_date <= in_30_days,
        )
    )
    expiring_memberships_count = res_expiring.scalar_one() or 0

    # 3. Today's Check-ins
    res_today_checkins = await db.execute(
        select(func.count(Checkin.id)).where(
            Checkin.tenant_id == tenant_id,
            Checkin.checkin_time >= today_start,
            Checkin.checkin_time < today_end,
        )
    )
    today_checkins_count = res_today_checkins.scalar_one() or 0

    # 4. Past Due Invoices
    res_past_due = await db.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(
                func.sum(Invoice.total_amount_minor - Invoice.paid_amount_minor), 0
            ),
        ).where(
            Invoice.tenant_id == tenant_id,
            Invoice.status == "OPEN",
            Invoice.due_date.is_not(None),
            Invoice.due_date < now,
        )
    )
    past_due_row = res_past_due.first()
    past_due_invoices_count = past_due_row[0] if past_due_row else 0
    past_due_invoices_amount_minor = int(past_due_row[1]) if past_due_row else 0

    # 5. Month Collected Revenue
    res_month_collected = await db.execute(
        select(func.coalesce(func.sum(Payment.amount_minor), 0)).where(
            Payment.tenant_id == tenant_id,
            Payment.status == "SUCCEEDED",
            Payment.created_at >= month_start,
        )
    )
    month_collected_amount_minor = int(res_month_collected.scalar_one() or 0)

    # 6. Total Outstanding Debt
    res_total_debt = await db.execute(
        select(
            func.coalesce(
                func.sum(Invoice.total_amount_minor - Invoice.paid_amount_minor), 0
            )
        ).where(
            Invoice.tenant_id == tenant_id,
            Invoice.status.in_(["OPEN", "PARTIALLY_PAID"]),
        )
    )
    total_outstanding_debt_minor = int(res_total_debt.scalar_one() or 0)

    return DashboardKPIResponse(
        active_members_count=active_members_count,
        expiring_memberships_count=expiring_memberships_count,
        today_checkins_count=today_checkins_count,
        past_due_invoices_count=past_due_invoices_count,
        past_due_invoices_amount_minor=past_due_invoices_amount_minor,
        month_collected_amount_minor=month_collected_amount_minor,
        total_outstanding_debt_minor=total_outstanding_debt_minor,
        currency="TRY",
    )
