"""user_sessions last_seen_at + last_step_up_at

Revision ID: xc4d5e6f7a8b
Revises: xb3c4d5e6f7a
Create Date: 2026-08-16 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "xc4d5e6f7a8b"
down_revision: str | Sequence[str] | None = "xb3c4d5e6f7a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_sessions",
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user_sessions",
        sa.Column("last_step_up_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_sessions", "last_step_up_at")
    op.drop_column("user_sessions", "last_seen_at")
