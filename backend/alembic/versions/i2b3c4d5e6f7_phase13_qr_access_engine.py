"""Phase 13: QR jti replay, signing key tenant-kid uniqueness, access expand

Revision ID: i2b3c4d5e6f7
Revises: h1a2b3c4d5e6
Create Date: 2026-08-09 22:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

revision: str = "i2b3c4d5e6f7"
down_revision: str | Sequence[str] | None = "h1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- signing_keys: algorithm + tenant-scoped kid uniqueness ---
    op.add_column(
        "signing_keys",
        sa.Column(
            "algorithm",
            sa.String(length=32),
            nullable=False,
            server_default="HMAC_SHA256",
        ),
    )
    # Expand secret-ref capacity (KMS ARNs / local:hmac refs)
    op.alter_column(
        "signing_keys",
        "key_material",
        existing_type=sa.String(length=200),
        type_=sa.String(length=512),
        existing_nullable=False,
    )
    # Drop global unique on kid if present; keep non-unique index for lookups
    op.execute("DROP INDEX IF EXISTS ix_signing_keys_kid")
    op.create_index("ix_signing_keys_kid", "signing_keys", ["kid"], unique=False)
    op.create_unique_constraint(
        "uq_signing_keys_tenant_kid", "signing_keys", ["tenant_id", "kid"]
    )

    # --- access_attempts expand ---
    op.add_column(
        "access_attempts",
        sa.Column("jti", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "access_attempts",
        sa.Column("method", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_access_attempts_jti", "access_attempts", ["jti"], unique=False)

    # --- qr_jti_replays ---
    op.create_table(
        "qr_jti_replays",
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=True),
        sa.Column("credential_id", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id", "member_id"],
            ["members.tenant_id", "members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_qr_jti_replays_tenant_id"),
        sa.UniqueConstraint("tenant_id", "jti", name="uq_qr_jti_replays_tenant_jti"),
    )
    op.create_index(
        op.f("ix_qr_jti_replays_tenant_id"),
        "qr_jti_replays",
        ["tenant_id"],
        unique=False,
    )
    enable_rls("qr_jti_replays")


def downgrade() -> None:
    disable_rls("qr_jti_replays")
    op.drop_index(op.f("ix_qr_jti_replays_tenant_id"), table_name="qr_jti_replays")
    op.drop_table("qr_jti_replays")

    op.drop_index("ix_access_attempts_jti", table_name="access_attempts")
    op.drop_column("access_attempts", "method")
    op.drop_column("access_attempts", "jti")

    op.drop_constraint("uq_signing_keys_tenant_kid", "signing_keys", type_="unique")
    op.drop_index("ix_signing_keys_kid", table_name="signing_keys")
    op.create_index("ix_signing_keys_kid", "signing_keys", ["kid"], unique=True)
    op.alter_column(
        "signing_keys",
        "key_material",
        existing_type=sa.String(length=512),
        type_=sa.String(length=200),
        existing_nullable=False,
    )
    op.drop_column("signing_keys", "algorithm")
