"""Federation / platform-level management and read surface. Implements ADR-043.

Every route here is organization-scoped from the caller's own role assignments.
Cross-tenant aggregates are computed one tenant at a time so the RLS boundary
stays exactly as it is — see FederationService.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import FederationScope, get_db, get_federation_scope
from app.services.federation import MAX_TENANT_PAGE, FederationService

router = APIRouter()


# ----- Schemas -----


class OrganizationSummary(BaseModel):
    id: UUID
    name: str
    domain: str | None


class TenantSummary(BaseModel):
    id: UUID
    name: str
    location_code: str
    organization_id: UUID
    status: str = "ACTIVE"
    suspended_at: datetime | None = None
    suspension_reason: str | None = None
    member_count: int
    active_membership_count: int
    # Money stays integer minor units end to end — never a float.
    revenue_minor: int


class TenantCreateRequest(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=2, max_length=100)
    location_code: str = Field(min_length=2, max_length=20)
    initial_branch_name: str | None = None
    initial_branch_address: str | None = None


class TenantSuspendRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class FederationSummary(BaseModel):
    organization_count: int
    tenant_count: int
    active_tenant_count: int
    suspended_tenant_count: int
    member_count: int
    active_membership_count: int
    revenue_minor: int
    # True when the figures cover only the returned page of tenants.
    partial: bool


class AuditEventSummary(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID | None
    action: str
    resource_type: str
    resource_id: UUID | None
    created_at: datetime


class PassportConfigResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    is_active: bool
    allowed_home_gym_tiers: str | None
    rules: dict | None
    updated_at: datetime | None = None


class PassportConfigUpdate(BaseModel):
    is_active: bool
    allowed_home_gym_tiers: str | None = None
    rules: dict = Field(default_factory=dict)


class ComplianceRecordCreate(BaseModel):
    certification_name: str = Field(min_length=2, max_length=100)
    status: str = Field(pattern="^(PASSED|FAILED|CONDITIONAL|EXPIRED)$")
    audit_date: datetime | None = None
    auditor_notes: str | None = None


class ComplianceRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    certification_name: str
    status: str
    audit_date: datetime
    auditor_notes: str | None
    created_at: datetime


class NetworkAlertCreate(BaseModel):
    organization_id: UUID
    target_tenant_id: UUID | None = None
    title: str = Field(min_length=3, max_length=150)
    message: str = Field(min_length=5, max_length=2000)
    severity: str = Field(
        default="INFO", pattern="^(INFO|WARNING|CRITICAL|MAINTENANCE)$"
    )


class NetworkAlertResponse(BaseModel):
    id: UUID
    organization_id: UUID
    target_tenant_id: UUID | None
    title: str
    message: str
    severity: str
    created_at: datetime


class AnalyticsOverviewResponse(BaseModel):
    total_checkins: int
    checkins_by_tenant: dict[str, int]
    total_revenue_minor: int
    revenue_by_tenant_minor: dict[str, int]
    partial: bool


# ----- Organization & Tenant Directory Routes -----


@router.get("/organizations", response_model=list[OrganizationSummary])
async def list_organizations(
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    orgs = await FederationService(db).list_organizations(scope.org_ids)
    return [OrganizationSummary(id=o.id, name=o.name, domain=o.domain) for o in orgs]


@router.get("/tenants", response_model=list[TenantSummary])
async def list_tenants(
    limit: int = Query(default=25, ge=1, le=MAX_TENANT_PAGE),
    offset: int = Query(default=0, ge=0),
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenants = await svc.list_tenants(scope.org_ids, limit=limit, offset=offset)
    if not tenants:
        return []

    metrics = await svc.metrics_for_tenants([t.id for t in tenants])
    return [
        TenantSummary(
            id=t.id,
            name=t.name,
            location_code=t.location_code,
            organization_id=t.organization_id,
            status=t.status,
            suspended_at=t.suspended_at,
            suspension_reason=t.suspension_reason,
            **metrics[t.id],
        )
        for t in tenants
    ]


@router.post(
    "/tenants", response_model=TenantSummary, status_code=status.HTTP_201_CREATED
)
async def create_tenant(
    body: TenantCreateRequest,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    """Provision a new gym tenant under an authorized organization."""
    if scope.org_ids is not None and body.organization_id not in scope.org_ids:
        raise HTTPException(
            status_code=403, detail="Bu organizasyon için kulüp oluşturma yetkiniz yok."
        )

    svc = FederationService(db)
    tenant = await svc.create_tenant(
        org_id=body.organization_id,
        name=body.name,
        location_code=body.location_code,
        initial_branch_name=body.initial_branch_name,
        initial_branch_address=body.initial_branch_address,
        actor_id=scope.user.id,
    )
    await db.commit()

    metrics = await svc.tenant_metrics(tenant.id)
    return TenantSummary(
        id=tenant.id,
        name=tenant.name,
        location_code=tenant.location_code,
        organization_id=tenant.organization_id,
        status=tenant.status,
        suspended_at=tenant.suspended_at,
        suspension_reason=tenant.suspension_reason,
        **metrics,
    )


@router.get("/tenants/{tenant_id}", response_model=TenantSummary)
async def get_tenant(
    tenant_id: UUID,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenant = await svc.get_tenant(tenant_id, scope.org_ids)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")

    metrics = await svc.metrics_for_tenants([tenant.id])
    return TenantSummary(
        id=tenant.id,
        name=tenant.name,
        location_code=tenant.location_code,
        organization_id=tenant.organization_id,
        status=tenant.status,
        suspended_at=tenant.suspended_at,
        suspension_reason=tenant.suspension_reason,
        **metrics[tenant.id],
    )


@router.post("/tenants/{tenant_id}/suspend", response_model=TenantSummary)
async def suspend_tenant(
    tenant_id: UUID,
    body: TenantSuspendRequest,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a tenant for policy or compliance violations."""
    svc = FederationService(db)
    tenant = await svc.get_tenant(tenant_id, scope.org_ids)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")

    tenant = await svc.suspend_tenant(
        tenant, reason=body.reason, actor_id=scope.user.id
    )
    await db.commit()

    metrics = await svc.tenant_metrics(tenant.id)
    return TenantSummary(
        id=tenant.id,
        name=tenant.name,
        location_code=tenant.location_code,
        organization_id=tenant.organization_id,
        status=tenant.status,
        suspended_at=tenant.suspended_at,
        suspension_reason=tenant.suspension_reason,
        **metrics,
    )


@router.post("/tenants/{tenant_id}/reactivate", response_model=TenantSummary)
async def reactivate_tenant(
    tenant_id: UUID,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    """Reactivate a suspended tenant."""
    svc = FederationService(db)
    tenant = await svc.get_tenant(tenant_id, scope.org_ids)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")

    tenant = await svc.reactivate_tenant(tenant, actor_id=scope.user.id)
    await db.commit()

    metrics = await svc.tenant_metrics(tenant.id)
    return TenantSummary(
        id=tenant.id,
        name=tenant.name,
        location_code=tenant.location_code,
        organization_id=tenant.organization_id,
        status=tenant.status,
        suspended_at=tenant.suspended_at,
        suspension_reason=tenant.suspension_reason,
        **metrics,
    )


# ----- Federation Summary & Audit -----


@router.get("/federation/summary", response_model=FederationSummary)
async def federation_summary(
    limit: int = Query(default=MAX_TENANT_PAGE, ge=1, le=MAX_TENANT_PAGE),
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    """Roll-up over one page of tenants."""
    svc = FederationService(db)
    orgs = await svc.list_organizations(scope.org_ids)
    tenants = await svc.list_tenants(scope.org_ids, limit=limit, offset=0)
    next_page = await svc.list_tenants(scope.org_ids, limit=1, offset=limit)

    metrics = await svc.metrics_for_tenants([t.id for t in tenants])
    active_count = sum(1 for t in tenants if t.status == "ACTIVE")
    suspended_count = sum(1 for t in tenants if t.status == "SUSPENDED")

    return FederationSummary(
        organization_count=len(orgs),
        tenant_count=len(tenants),
        active_tenant_count=active_count,
        suspended_tenant_count=suspended_count,
        member_count=sum(m["member_count"] for m in metrics.values()),
        active_membership_count=sum(
            m["active_membership_count"] for m in metrics.values()
        ),
        revenue_minor=sum(m["revenue_minor"] for m in metrics.values()),
        partial=bool(next_page),
    )


@router.get("/audit", response_model=list[AuditEventSummary])
async def list_audit_events(
    limit_per_tenant: int = Query(default=20, ge=1, le=100),
    tenant_limit: int = Query(default=10, ge=1, le=MAX_TENANT_PAGE),
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenants = await svc.list_tenants(scope.org_ids, limit=tenant_limit, offset=0)
    if not tenants:
        return []
    events = await svc.recent_audit_events(
        [t.id for t in tenants], limit_per_tenant=limit_per_tenant
    )
    return [
        AuditEventSummary(
            id=e.id,
            tenant_id=e.tenant_id,
            user_id=e.user_id,
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            created_at=e.created_at,
        )
        for e in events
    ]


# ----- Federation Passport Routes -----


@router.get("/passport/configs", response_model=list[PassportConfigResponse])
async def list_passport_configs(
    limit: int = Query(default=MAX_TENANT_PAGE, ge=1, le=MAX_TENANT_PAGE),
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    """List passport roaming configs across authorized federation tenants."""
    svc = FederationService(db)
    tenants = await svc.list_tenants(scope.org_ids, limit=limit, offset=0)
    if not tenants:
        return []
    configs = await svc.network_passport_rules([t.id for t in tenants])
    return [
        PassportConfigResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            is_active=c.is_active,
            allowed_home_gym_tiers=c.allowed_home_gym_tiers,
            rules=c.rules,
            updated_at=c.updated_at,
        )
        for c in configs
    ]


@router.get("/tenants/{tenant_id}/passport", response_model=PassportConfigResponse)
async def get_tenant_passport(
    tenant_id: UUID,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenant = await svc.get_tenant(tenant_id, scope.org_ids)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")

    config = await svc.get_passport_config(tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="passport_config_not_found")

    return PassportConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        is_active=config.is_active,
        allowed_home_gym_tiers=config.allowed_home_gym_tiers,
        rules=config.rules,
        updated_at=config.updated_at,
    )


@router.put("/tenants/{tenant_id}/passport", response_model=PassportConfigResponse)
async def update_tenant_passport(
    tenant_id: UUID,
    body: PassportConfigUpdate,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenant = await svc.get_tenant(tenant_id, scope.org_ids)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")

    config = await svc.update_passport_config(
        tenant_id=tenant_id,
        is_active=body.is_active,
        allowed_home_gym_tiers=body.allowed_home_gym_tiers,
        rules=body.rules,
    )
    await db.commit()

    return PassportConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        is_active=config.is_active,
        allowed_home_gym_tiers=config.allowed_home_gym_tiers,
        rules=config.rules,
        updated_at=config.updated_at,
    )


# ----- Compliance & Auditing Routes -----


@router.get("/compliance", response_model=list[ComplianceRecordResponse])
async def list_compliance_records(
    limit_per_tenant: int = Query(default=10, ge=1, le=50),
    tenant_limit: int = Query(default=25, ge=1, le=MAX_TENANT_PAGE),
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenants = await svc.list_tenants(scope.org_ids, limit=tenant_limit, offset=0)
    if not tenants:
        return []
    records = await svc.list_compliance_records(
        [t.id for t in tenants], limit_per_tenant=limit_per_tenant
    )
    return [
        ComplianceRecordResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            certification_name=r.certification_name,
            status=r.status,
            audit_date=r.audit_date,
            auditor_notes=r.auditor_notes,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post(
    "/tenants/{tenant_id}/compliance",
    response_model=ComplianceRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_compliance_record(
    tenant_id: UUID,
    body: ComplianceRecordCreate,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenant = await svc.get_tenant(tenant_id, scope.org_ids)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant_not_found")

    record = await svc.create_compliance_record(
        tenant_id=tenant_id,
        certification_name=body.certification_name,
        status=body.status,
        audit_date=body.audit_date,
        auditor_notes=body.auditor_notes,
    )
    await db.commit()

    return ComplianceRecordResponse(
        id=record.id,
        tenant_id=record.tenant_id,
        certification_name=record.certification_name,
        status=record.status,
        audit_date=record.audit_date,
        auditor_notes=record.auditor_notes,
        created_at=record.created_at,
    )


# ----- Network Alerts Routes -----


@router.get("/alerts", response_model=list[NetworkAlertResponse])
async def list_network_alerts(
    tenant_id: UUID | None = None,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    alerts = await svc.list_network_alerts(scope.org_ids, tenant_id=tenant_id)
    return [
        NetworkAlertResponse(
            id=a.id,
            organization_id=a.organization_id,
            target_tenant_id=a.target_tenant_id,
            title=a.title,
            message=a.message,
            severity=a.severity,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.post(
    "/alerts",
    response_model=NetworkAlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_network_alert(
    body: NetworkAlertCreate,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    if scope.org_ids is not None and body.organization_id not in scope.org_ids:
        raise HTTPException(
            status_code=403, detail="Bu organizasyona duyuru yayınlama yetkiniz yok."
        )

    svc = FederationService(db)
    alert = await svc.create_network_alert(
        org_id=body.organization_id,
        title=body.title,
        message=body.message,
        severity=body.severity,
        target_tenant_id=body.target_tenant_id,
    )
    await db.commit()

    return NetworkAlertResponse(
        id=alert.id,
        organization_id=alert.organization_id,
        target_tenant_id=alert.target_tenant_id,
        title=alert.title,
        message=alert.message,
        severity=alert.severity,
        created_at=alert.created_at,
    )


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_network_alert(
    alert_id: UUID,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    deleted = await svc.delete_network_alert(alert_id, scope.org_ids)
    if not deleted:
        raise HTTPException(status_code=404, detail="alert_not_found")
    await db.commit()


# ----- Cross-Tenant Analytics & Reports -----


@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
async def analytics_overview(
    limit: int = Query(default=MAX_TENANT_PAGE, ge=1, le=MAX_TENANT_PAGE),
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenants = await svc.list_tenants(scope.org_ids, limit=limit, offset=0)
    next_page = await svc.list_tenants(scope.org_ids, limit=1, offset=limit)

    tenant_ids = [t.id for t in tenants]
    checkins_by_tenant = await svc.cross_tenant_checkins(tenant_ids)
    revenue_by_tenant = await svc.cross_tenant_revenue(tenant_ids)

    return AnalyticsOverviewResponse(
        total_checkins=sum(checkins_by_tenant.values()),
        checkins_by_tenant=checkins_by_tenant,
        total_revenue_minor=sum(revenue_by_tenant.values()),
        revenue_by_tenant_minor=revenue_by_tenant,
        partial=bool(next_page),
    )
