"""Federation-scope reads and governance. Implements ADR-043.

Cross-tenant aggregates and tenant-owned mutations are executed by visiting one
tenant at a time — the RLS GUC still holds exactly one tenant for every statement
issued. No policy is widened and no RLS-bypassing role is used.
See docs/adr/ADR-043-federation-scope-reads.md.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access import Checkin
from app.models.audit import AuditEvent
from app.models.federation import ComplianceRecord, NetworkAlert, PassportConfig
from app.models.finance import Payment, PaymentStatus
from app.models.location import Location
from app.models.member import Member
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.tenant import Tenant, TenantStatus

# Hard ceiling on how many tenants one request may aggregate over. The loop
# costs one round-trip per tenant, so this is what keeps latency bounded.
MAX_TENANT_PAGE = 50


class FederationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----- directory (no RLS on tenants/organizations/network_alerts) -----

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

    # ----- Tenant Lifecycle Mutations -----

    async def create_tenant(
        self,
        org_id: UUID,
        name: str,
        location_code: str,
        initial_branch_name: str | None = None,
        initial_branch_address: str | None = None,
        actor_id: UUID | None = None,
    ) -> Tenant:
        """Provision a new tenant, default branch, and default passport config."""
        tenant = Tenant(
            id=uuid4(),
            organization_id=org_id,
            name=name,
            location_code=location_code,
            status=TenantStatus.ACTIVE.value,
        )
        self.db.add(tenant)
        await self.db.flush()

        # Create initial default location/branch under per-tenant RLS
        await self._enter_tenant(tenant.id)
        try:
            location = Location(
                id=uuid4(),
                tenant_id=tenant.id,
                name=initial_branch_name or f"{name} Ana Şube",
                timezone="Europe/Istanbul",
                address=initial_branch_address,
            )
            self.db.add(location)

            passport = PassportConfig(
                id=uuid4(),
                tenant_id=tenant.id,
                is_active=False,
                allowed_home_gym_tiers="VIP,GOLD",
                rules={"max_monthly_roaming_visits": 5, "guest_fee_minor": 0},
            )
            self.db.add(passport)

            event = AuditEvent(
                id=uuid4(),
                tenant_id=tenant.id,
                user_id=actor_id,
                action="tenant.provisioned",
                resource_type="Tenant",
                resource_id=tenant.id,
            )
            self.db.add(event)
            await self.db.flush()
        finally:
            await self._leave_tenant()

        return tenant

    async def suspend_tenant(
        self, tenant: Tenant, reason: str, actor_id: UUID | None = None
    ) -> Tenant:
        """Suspend a tenant and record an audit event."""
        tenant.status = TenantStatus.SUSPENDED.value
        tenant.suspended_at = datetime.now(UTC)
        tenant.suspension_reason = reason
        self.db.add(tenant)

        await self._record_tenant_audit(
            tenant.id,
            action="tenant.suspended",
            user_id=actor_id,
        )
        await self.db.flush()
        return tenant

    async def reactivate_tenant(
        self, tenant: Tenant, actor_id: UUID | None = None
    ) -> Tenant:
        """Reactivate a suspended tenant and record an audit event."""
        tenant.status = TenantStatus.ACTIVE.value
        tenant.suspended_at = None
        tenant.suspension_reason = None
        self.db.add(tenant)

        await self._record_tenant_audit(
            tenant.id,
            action="tenant.reactivated",
            user_id=actor_id,
        )
        await self.db.flush()
        return tenant

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
                    Payment.status.in_(
                        [PaymentStatus.SUCCEEDED.value, PaymentStatus.PARTIALLY_REFUNDED.value]
                    ),
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

    # ----- Federation Passport (Cross-Club Roaming) -----

    async def get_passport_config(self, tenant_id: UUID) -> PassportConfig | None:
        """Retrieve passport config under per-tenant RLS context."""
        await self._enter_tenant(tenant_id)
        try:
            stmt = select(PassportConfig).where(PassportConfig.tenant_id == tenant_id)
            result = await self.db.execute(stmt)
            return result.scalars().first()
        finally:
            await self._leave_tenant()

    async def update_passport_config(
        self,
        tenant_id: UUID,
        is_active: bool,
        allowed_home_gym_tiers: str | None,
        rules: dict | None,
    ) -> PassportConfig:
        """Upsert passport config under per-tenant RLS context."""
        await self._enter_tenant(tenant_id)
        try:
            stmt = select(PassportConfig).where(PassportConfig.tenant_id == tenant_id)
            result = await self.db.execute(stmt)
            config = result.scalars().first()
            if not config:
                config = PassportConfig(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    is_active=is_active,
                    allowed_home_gym_tiers=allowed_home_gym_tiers,
                    rules=rules or {},
                )
                self.db.add(config)
            else:
                config.is_active = is_active
                config.allowed_home_gym_tiers = allowed_home_gym_tiers
                config.rules = rules or {}
                self.db.add(config)
            await self.db.flush()
            return config
        finally:
            await self._leave_tenant()

    async def network_passport_rules(
        self, tenant_ids: list[UUID]
    ) -> list[PassportConfig]:
        """Aggregate passport configs across paged tenants (ADR-043 loop)."""
        if len(tenant_ids) > MAX_TENANT_PAGE:
            raise ValueError("tenant page exceeds MAX_TENANT_PAGE")
        configs: list[PassportConfig] = []
        try:
            for tid in tenant_ids:
                await self._enter_tenant(tid)
                result = await self.db.execute(
                    select(PassportConfig).where(PassportConfig.tenant_id == tid)
                )
                cfg = result.scalars().first()
                if cfg:
                    configs.append(cfg)
        finally:
            await self._leave_tenant()
        return configs

    # ----- Compliance & Audits -----

    async def create_compliance_record(
        self,
        tenant_id: UUID,
        certification_name: str,
        status: str,
        audit_date: datetime | None,
        auditor_notes: str | None,
    ) -> ComplianceRecord:
        """Write compliance record under per-tenant RLS."""
        await self._enter_tenant(tenant_id)
        try:
            record = ComplianceRecord(
                id=uuid4(),
                tenant_id=tenant_id,
                certification_name=certification_name,
                status=status,
                audit_date=audit_date or datetime.now(UTC),
                auditor_notes=auditor_notes,
            )
            self.db.add(record)
            await self.db.flush()
            return record
        finally:
            await self._leave_tenant()

    async def list_compliance_records(
        self, tenant_ids: list[UUID], limit_per_tenant: int = 20
    ) -> list[ComplianceRecord]:
        """Cross-tenant compliance records via ADR-043 loop."""
        if len(tenant_ids) > MAX_TENANT_PAGE:
            raise ValueError("tenant page exceeds MAX_TENANT_PAGE")
        records: list[ComplianceRecord] = []
        try:
            for tid in tenant_ids:
                await self._enter_tenant(tid)
                result = await self.db.execute(
                    select(ComplianceRecord)
                    .where(ComplianceRecord.tenant_id == tid)
                    .order_by(ComplianceRecord.audit_date.desc())
                    .limit(limit_per_tenant)
                )
                records.extend(result.scalars().all())
        finally:
            await self._leave_tenant()
        records.sort(key=lambda r: r.audit_date, reverse=True)
        return records

    # ----- Network Alerts Broadcast -----

    async def list_network_alerts(
        self, org_ids: list[UUID] | None, tenant_id: UUID | None = None
    ) -> list[NetworkAlert]:
        """Read organization-level alerts (no tenant RLS; org scoped)."""
        stmt = select(NetworkAlert).order_by(NetworkAlert.created_at.desc())
        if org_ids is not None:
            if not org_ids:
                return []
            stmt = stmt.where(NetworkAlert.organization_id.in_(org_ids))
        if tenant_id is not None:
            stmt = stmt.where(
                (NetworkAlert.target_tenant_id == tenant_id)
                | (NetworkAlert.target_tenant_id.is_(None))
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_network_alert(
        self,
        org_id: UUID,
        title: str,
        message: str,
        severity: str = "INFO",
        target_tenant_id: UUID | None = None,
    ) -> NetworkAlert:
        alert = NetworkAlert(
            id=uuid4(),
            organization_id=org_id,
            target_tenant_id=target_tenant_id,
            title=title,
            message=message,
            severity=severity,
        )
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def delete_network_alert(
        self, alert_id: UUID, org_ids: list[UUID] | None
    ) -> bool:
        stmt = select(NetworkAlert).where(NetworkAlert.id == alert_id)
        if org_ids is not None:
            stmt = stmt.where(NetworkAlert.organization_id.in_(org_ids))
        alert = (await self.db.execute(stmt)).scalars().first()
        if not alert:
            return False
        await self.db.delete(alert)
        await self.db.flush()
        return True

    # ----- Cross-Tenant Analytics -----

    async def cross_tenant_checkins(
        self,
        tenant_ids: list[UUID],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        """Cross-tenant checkin volume via ADR-043 per-tenant iteration."""
        if len(tenant_ids) > MAX_TENANT_PAGE:
            raise ValueError("tenant page exceeds MAX_TENANT_PAGE")
        by_tenant: dict[str, int] = {}
        try:
            for tid in tenant_ids:
                await self._enter_tenant(tid)
                stmt = select(func.count(Checkin.id)).where(Checkin.tenant_id == tid)
                if start_date is not None:
                    stmt = stmt.where(Checkin.checkin_time >= start_date)
                if end_date is not None:
                    stmt = stmt.where(Checkin.checkin_time <= end_date)
                count = (await self.db.execute(stmt)).scalar_one()
                by_tenant[str(tid)] = int(count)
        finally:
            await self._leave_tenant()
        return by_tenant

    async def cross_tenant_revenue(
        self,
        tenant_ids: list[UUID],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, int]:
        """Cross-tenant payment revenue via ADR-043 loop (integer minor units)."""
        if len(tenant_ids) > MAX_TENANT_PAGE:
            raise ValueError("tenant page exceeds MAX_TENANT_PAGE")
        by_tenant: dict[str, int] = {}
        try:
            for tid in tenant_ids:
                await self._enter_tenant(tid)
                stmt = select(func.coalesce(func.sum(Payment.amount_minor), 0)).where(
                    Payment.tenant_id == tid,
                    Payment.status.in_(
                        [PaymentStatus.SUCCEEDED.value, PaymentStatus.PARTIALLY_REFUNDED.value]
                    ),
                )
                if start_date is not None:
                    stmt = stmt.where(Payment.created_at >= start_date)
                if end_date is not None:
                    stmt = stmt.where(Payment.created_at <= end_date)
                captured = (await self.db.execute(stmt)).scalar_one()
                by_tenant[str(tid)] = int(captured)
        finally:
            await self._leave_tenant()
        return by_tenant

    # Helper for audit log
    async def _record_tenant_audit(
        self,
        tenant_id: UUID,
        action: str,
        user_id: UUID | None = None,
    ) -> None:
        await self._enter_tenant(tenant_id)
        try:
            event = AuditEvent(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type="Tenant",
                resource_id=tenant_id,
            )
            self.db.add(event)
            await self.db.flush()
        finally:
            await self._leave_tenant()
