"""enable RLS on audit_events

audit_events carries tenant_id but had no RLS. It was previously unreachable
over HTTP so nothing leaked; GET /admin/audit gives it a read surface for the
first time, so it gets the same isolation as every other tenant-owned table
rather than an exemption (ADR-031).

device_sessions is deliberately left without RLS: get_current_device must look
a session up *before* any tenant context exists, so a tenant policy there would
fail closed on every device request. It is keyed by a hashed bearer token.

Revision ID: t3a4b5c6d7e8
Revises: s2f3a4b5c6d7
Create Date: 2026-08-11 01:00:00.000000

"""

from collections.abc import Sequence

from app.db.rls import disable_rls, enable_rls

revision: str = "t3a4b5c6d7e8"
down_revision: str | Sequence[str] | None = "s2f3a4b5c6d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    enable_rls("audit_events")


def downgrade() -> None:
    disable_rls("audit_events")
