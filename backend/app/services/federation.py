"""Federation-scope reads. Implements ADR-043.

Cross-tenant aggregates are produced by visiting one tenant at a time — the RLS
GUC still holds exactly one tenant for every statement issued. No policy is
widened and no RLS-bypassing role is used. See docs/adr/ADR-043-federation-scope-reads.md.
"""

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.finance import Payment
from app.models.member import Member
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.tenant import Tenant

# Hard ceiling on how many tenants one request may aggregate over. The loop
# costs one round-trip per tenant, so this is what keeps latency bounded.
MAX_TENANT_PAGE = 50


class FederationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----- directory (no RLS on tenants/organizations) -----

    async def list_organizations(
        self, org_ids: list[UUID] | None
    ) -> list[Organization]:
        """``org_ids=None`` means platform scope (every organization)."""
        stmt = select(Organization).order_by(Organization.name)
        if org_ids is not None:
            if not org_ids:
                return []
            stmt = stmt.where(Organization.id.in_(org_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_tenants(
        self,
        org_ids: list[UUID] | None,
        *,
        limit: int = MAX_TENANT_PAGE,
        offset: int = 0,
    ) -> list[Tenant]:
        limit = max(1, min(limit, MAX_TENANT_PAGE))
        offset = max(0, offset)
        stmt = select(Tenant).order_by(Tenant.name)
        if org_ids is not None:
            if not org_ids:
                return []
            stmt = stmt.where(Tenant.organization_id.in_(org_ids))
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_tenant(
        self, tenant_id: UUID, org_ids: list[UUID] | None
    ) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        if org_ids is not None:
            if not org_ids:
                return None
            stmt = stmt.where(Tenant.organization_id.in_(org_ids))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    # ----- per-tenant aggregates (ADR-043 path 2) -----

    async def _enter_tenant(self, tenant_id: UUID) -> None:
        await self.db.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )

    async def _leave_tenant(self) -> None:
        """Clear the GUC so no tenant context outlives the loop."""
        await self.db.execute(
            text("SELECT set_config('app.current_tenant_id', '', true)")
        )

    async def tenant_metrics(self, tenant_id: UUID) -> dict[str, int]:
        """Counts for one tenant. Caller is responsible for the surrounding loop."""
        await self._enter_tenant(tenant_id)

        member_count = (
            await self.db.execute(
                select(func.count())
                .select_from(Member)
                .where(Member.tenant_id == tenant_id)
            )
        ).scalar_one()

        active_memberships = (
            await self.db.execute(
                select(func.count())
                .select_from(Membership)
                .where(
                    Membership.tenant_id == tenant_id,
                    Membership.status == "ACTIVE",
                )
            )
        ).scalar_one()

        # amount_minor only — never a float, per the money rule.
        revenue_minor = (
            await self.db.execute(
                select(func.coalesce(func.sum(Payment.amount_minor), 0)).where(
                    Payment.tenant_id == tenant_id,
                    Payment.status == "CAPTURED",
                )
            )
        ).scalar_one()

        return {
            "member_count": int(member_count),
            "active_membership_count": int(active_memberships),
            "revenue_minor": int(revenue_minor),
        }

    async def metrics_for_tenants(
        self, tenant_ids: list[UUID]
    ) -> dict[UUID, dict[str, int]]:
        """Read-only aggregate loop. Never mutates; never commits mid-loop."""
        if len(tenant_ids) > MAX_TENANT_PAGE:
            raise ValueError("tenant page exceeds MAX_TENANT_PAGE")
        out: dict[UUID, dict[str, int]] = {}
        try:
            for tenant_id in tenant_ids:
                out[tenant_id] = await self.tenant_metrics(tenant_id)
        finally:
            await self._leave_tenant()
        return out

    async def recent_audit_events(
        self, tenant_ids: list[UUID], *, limit_per_tenant: int = 20
    ) -> list[AuditEvent]:
        """audit_events is RLS-protected, so it is read the same per-tenant way."""
        if len(tenant_ids) > MAX_TENANT_PAGE:
            raise ValueError("tenant page exceeds MAX_TENANT_PAGE")
        limit_per_tenant = max(1, min(limit_per_tenant, 100))
        events: list[AuditEvent] = []
        try:
            for tenant_id in tenant_ids:
                await self._enter_tenant(tenant_id)
                result = await self.db.execute(
                    select(AuditEvent)
                    .where(AuditEvent.tenant_id == tenant_id)
                    .order_by(AuditEvent.created_at.desc())
                    .limit(limit_per_tenant)
                )
                events.extend(result.scalars().all())
        finally:
            await self._leave_tenant()
        events.sort(key=lambda e: e.created_at, reverse=True)
        return events
