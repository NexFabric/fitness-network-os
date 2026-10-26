"""Add federation performance indexes.

Revision ID: xa1b2c3d4e5f
Revises: x9c0d1e2f3a4
Create Date: 2026-08-15 17:50:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "xa1b2c3d4e5f"
down_revision = "x9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Tenant lookup by organization
    op.create_index(
        "ix_tenants_organization_id",
        "tenants",
        ["organization_id"],
        if_not_exists=True,
    )

    # 2. Network alert lookup by org and target
    op.create_index(
        "ix_network_alerts_org_target",
        "network_alerts",
        ["organization_id", "target_tenant_id"],
        if_not_exists=True,
    )

    # 3. Compliance audit records lookup ordered by audit_date
    op.create_index(
        "ix_compliance_records_tenant_audit_date",
        "compliance_records",
        ["tenant_id", "audit_date"],
        if_not_exists=True,
    )

    # 4. Checkins lookup ordered by time
    op.create_index(
        "ix_checkins_tenant_time",
        "checkins",
        ["tenant_id", "checkin_time"],
        if_not_exists=True,
    )

    # 5. Audit events recent lookup
    op.create_index(
        "ix_audit_events_tenant_created",
        "audit_events",
        ["tenant_id", "created_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_events_tenant_created", table_name="audit_events", if_exists=True
    )
    op.drop_index("ix_checkins_tenant_time", table_name="checkins", if_exists=True)
    op.drop_index(
        "ix_compliance_records_tenant_audit_date",
        table_name="compliance_records",
        if_exists=True,
    )
    op.drop_index(
        "ix_network_alerts_org_target", table_name="network_alerts", if_exists=True
    )
    op.drop_index("ix_tenants_organization_id", table_name="tenants", if_exists=True)
