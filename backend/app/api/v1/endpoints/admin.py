"""Federation / platform-level read surface. Implements ADR-031.

Every route here is read-only and organization-scoped from the caller's own role
assignments. Cross-tenant aggregates are computed one tenant at a time so the
RLS boundary stays exactly as it is — see FederationService.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import FederationScope, get_db, get_federation_scope
from app.services.federation import MAX_TENANT_PAGE, FederationService

router = APIRouter()


class OrganizationSummary(BaseModel):
    id: UUID
    name: str
    domain: str | None


class TenantSummary(BaseModel):
    id: UUID
    name: str
    location_code: str
    organization_id: UUID
    member_count: int
    active_membership_count: int
    # Money stays integer minor units end to end — never a float.
    revenue_minor: int


class FederationSummary(BaseModel):
    organization_count: int
    tenant_count: int
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


@router.get("/organizations", response_model=list[OrganizationSummary])
async def list_organizations(
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    orgs = await FederationService(db).list_organizations(scope.org_ids)
    return [
        OrganizationSummary(id=o.id, name=o.name, domain=o.domain) for o in orgs
    ]


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
            **metrics[t.id],
        )
        for t in tenants
    ]


@router.get("/tenants/{tenant_id}", response_model=TenantSummary)
async def get_tenant(
    tenant_id: UUID,
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    svc = FederationService(db)
    tenant = await svc.get_tenant(tenant_id, scope.org_ids)
    if tenant is None:
        # Same 404 whether the tenant is absent or out of scope — do not let a
        # federation admin probe for the existence of other organizations.
        raise HTTPException(status_code=404, detail="tenant_not_found")

    metrics = await svc.metrics_for_tenants([tenant.id])
    return TenantSummary(
        id=tenant.id,
        name=tenant.name,
        location_code=tenant.location_code,
        organization_id=tenant.organization_id,
        **metrics[tenant.id],
    )


@router.get("/federation/summary", response_model=FederationSummary)
async def federation_summary(
    limit: int = Query(default=MAX_TENANT_PAGE, ge=1, le=MAX_TENANT_PAGE),
    scope: FederationScope = Depends(get_federation_scope),
    db: AsyncSession = Depends(get_db),
):
    """Roll-up over one page of tenants.

    ``partial`` says plainly when more tenants exist than were counted, so the
    UI can never present a page total as a platform total.
    """
    svc = FederationService(db)
    orgs = await svc.list_organizations(scope.org_ids)
    tenants = await svc.list_tenants(scope.org_ids, limit=limit, offset=0)
    next_page = await svc.list_tenants(scope.org_ids, limit=1, offset=limit)

    metrics = await svc.metrics_for_tenants([t.id for t in tenants])
    return FederationSummary(
        organization_count=len(orgs),
        tenant_count=len(tenants),
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
