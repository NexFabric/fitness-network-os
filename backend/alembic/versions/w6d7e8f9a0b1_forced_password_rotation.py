"""Forced password rotation for provisioned accounts.

An administrator can now create a staff account, which issues a one-time
password. That password must not stay valid indefinitely, so accounts carry a
``must_change_password`` flag and login hands them a restricted
``password_reset`` session that reaches only the change-password endpoint.

Revision ID: w6d7e8f9a0b1
Revises: v5c6d7e8f9a0
Create Date: 2026-08-13 19:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "w6d7e8f9a0b1"
down_revision: str | Sequence[str] | None = "v5c6d7e8f9a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.drop_constraint("ck_user_sessions_auth_level", "user_sessions", type_="check")
    op.create_check_constraint(
        "ck_user_sessions_auth_level",
        "user_sessions",
        "auth_level IN ('full', 'mfa_setup', 'password_reset')",
    )


def downgrade() -> None:
    # Restricted sessions become meaningless once the level is gone; revoke them
    # rather than leaving rows that violate the narrower constraint.
    op.execute(
        "UPDATE user_sessions SET is_revoked = true WHERE auth_level = 'password_reset'"
    )
    op.execute(
        "UPDATE user_sessions SET auth_level = 'full' "
        "WHERE auth_level = 'password_reset'"
    )
    op.drop_constraint("ck_user_sessions_auth_level", "user_sessions", type_="check")
    op.create_check_constraint(
        "ck_user_sessions_auth_level",
        "user_sessions",
        "auth_level IN ('full', 'mfa_setup')",
    )
    op.drop_column("users", "must_change_password")
