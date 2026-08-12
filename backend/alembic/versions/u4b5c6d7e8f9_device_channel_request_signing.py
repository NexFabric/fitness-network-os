"""Device channel request signing: per-session signing secret + nonce store

A stolen ``device_session`` cookie was previously a complete credential for the
full 30-day session lifetime. Requests now carry an HMAC-SHA256 signature keyed
on a per-session secret the device receives once at ``POST /devices/auth``, and
``device_nonces`` makes each signed request single-use inside its timestamp
window (ADR-031).

The column is nullable so sessions issued before this migration keep resolving;
``get_current_device`` rejects them (401 ``device_session_unsigned``) and the
device re-authenticates to obtain signing material.

Revision ID: u4b5c6d7e8f9
Revises: t3a4b5c6d7e8
Create Date: 2026-08-12 11:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "u4b5c6d7e8f9"
down_revision: str | Sequence[str] | None = "t3a4b5c6d7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "device_sessions",
        sa.Column("signing_key_material", sa.String(length=512), nullable=True),
    )

    op.create_table(
        "device_nonces",
        sa.Column("device_session_id", sa.Uuid(), nullable=False),
        sa.Column("nonce", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_device_nonces_tenant_id"),
        sa.UniqueConstraint(
            "tenant_id",
            "device_session_id",
            "nonce",
            name="uq_device_nonces_session_nonce",
        ),
    )
    op.create_index(
        op.f("ix_device_nonces_tenant_id"), "device_nonces", ["tenant_id"], unique=False
    )
    # Expiry sweep runs on every signed request; without this it is a seq scan.
    op.create_index(
        "ix_device_nonces_expires_at", "device_nonces", ["expires_at"], unique=False
    )
    enable_rls("device_nonces")


def downgrade() -> None:
    disable_rls("device_nonces")
    op.drop_index("ix_device_nonces_expires_at", table_name="device_nonces")
    op.drop_index(op.f("ix_device_nonces_tenant_id"), table_name="device_nonces")
    op.drop_table("device_nonces")
    op.drop_column("device_sessions", "signing_key_material")
