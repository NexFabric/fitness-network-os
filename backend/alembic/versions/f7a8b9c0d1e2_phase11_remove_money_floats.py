"""Phase 11 remove money floats

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-08-09 21:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: str | Sequence[str] | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Opportunity money: float major → integer minor + currency
    op.add_column(
        "opportunities",
        sa.Column("value_amount_minor", sa.Integer(), nullable=True),
    )
    op.add_column(
        "opportunities",
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="TRY"),
    )
    # Convert existing float majors to minor (×100, half-up via ROUND)
    op.execute(
        """
        UPDATE opportunities
        SET value_amount_minor = ROUND(value * 100)::integer
        WHERE value IS NOT NULL
        """
    )
    op.drop_column("opportunities", "value")

    # Retention analytics: float probability → integer basis points
    op.add_column(
        "retention_cockpit",
        sa.Column("churn_probability_bps", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE retention_cockpit
        SET churn_probability_bps = LEAST(
            10000,
            GREATEST(0, ROUND(churn_probability * 10000)::integer)
        )
        WHERE churn_probability IS NOT NULL
        """
    )
    op.drop_column("retention_cockpit", "churn_probability")

    op.create_check_constraint(
        "ck_opportunities_value_amount_minor_nonneg",
        "opportunities",
        "value_amount_minor IS NULL OR value_amount_minor >= 0",
    )
    op.create_check_constraint(
        "ck_retention_churn_bps_range",
        "retention_cockpit",
        "churn_probability_bps IS NULL OR "
        "(churn_probability_bps >= 0 AND churn_probability_bps <= 10000)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_retention_churn_bps_range", "retention_cockpit")
    op.drop_constraint("ck_opportunities_value_amount_minor_nonneg", "opportunities")

    op.add_column(
        "retention_cockpit",
        sa.Column("churn_probability", sa.Float(), nullable=True),
    )
    op.execute(
        """
        UPDATE retention_cockpit
        SET churn_probability = churn_probability_bps::float / 10000.0
        WHERE churn_probability_bps IS NOT NULL
        """
    )
    op.drop_column("retention_cockpit", "churn_probability_bps")

    op.add_column(
        "opportunities",
        sa.Column("value", sa.Float(), nullable=True),
    )
    op.execute(
        """
        UPDATE opportunities
        SET value = value_amount_minor::float / 100.0
        WHERE value_amount_minor IS NOT NULL
        """
    )
    op.drop_column("opportunities", "currency")
    op.drop_column("opportunities", "value_amount_minor")
