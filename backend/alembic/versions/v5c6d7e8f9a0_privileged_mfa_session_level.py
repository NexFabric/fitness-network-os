"""Add restricted session level for privileged MFA enrollment.

Revision ID: v5c6d7e8f9a0
Revises: u4b5c6d7e8f9
Create Date: 2026-08-13 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "v5c6d7e8f9a0"
down_revision: str | Sequence[str] | None = "u4b5c6d7e8f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_sessions",
        sa.Column(
            "auth_level",
            sa.String(length=32),
            server_default="full",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_user_sessions_auth_level",
        "user_sessions",
        "auth_level IN ('full', 'mfa_setup')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_sessions_auth_level", "user_sessions", type_="check")
    op.drop_column("user_sessions", "auth_level")
