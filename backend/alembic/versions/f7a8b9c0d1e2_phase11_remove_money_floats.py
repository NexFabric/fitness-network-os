"""Phase 11 EXPAND: money floats → amount_minor / bps (no DROP)

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-08-09 21:00:00.000000

EXPAND / CONTRACT policy (PRODUCTION_READINESS):
  This revision only ADDS new columns and BACKFILLs them.
  Legacy float columns remain until a future CONTRACT migration is *created
  as a NEW revision* from the then-current head (never edit this file after
  merge to inject DROP):
    - opportunities.value
    - retention_cockpit.churn_probability

Assumption:
  Historical Opportunity.value values before Phase 11 are assumed TRY.
  No multi-currency existed on Opportunity pre-Phase 11.

PRE-PRODUCTION MIGRATION EXCEPTION:
  No live rolling multi-version deployment is supported for this expand.
  Concurrent old-version writers after backfill are NOT supported.
  The EXPAND/CONTRACT *shape* establishes the production standard; this
  revision does not claim zero-downtime dual-write coexistence.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: str | Sequence[str] | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- opportunities: expand (keep value Float until contract) ---
    op.add_column(
        "opportunities",
        sa.Column("value_amount_minor", sa.Integer(), nullable=True),
    )
    op.add_column(
        "opportunities",
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default="TRY"
        ),
    )
    # Backfill: major float → minor int (×100, half-up). Currency default TRY.
    op.execute(
        """
        UPDATE opportunities
        SET value_amount_minor = ROUND(value * 100)::integer,
            currency = COALESCE(currency, 'TRY')
        WHERE value IS NOT NULL
        """
    )
    op.create_check_constraint(
        "ck_opportunities_value_amount_minor_nonneg",
        "opportunities",
        "value_amount_minor IS NULL OR value_amount_minor >= 0",
    )

    # --- retention_cockpit: expand (keep churn_probability Float until contract) ---
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
    op.create_check_constraint(
        "ck_retention_churn_bps_range",
        "retention_cockpit",
        "churn_probability_bps IS NULL OR "
        "(churn_probability_bps >= 0 AND churn_probability_bps <= 10000)",
    )

    # NOTE: Do NOT drop opportunities.value or retention_cockpit.churn_probability here.
    # CONTRACT migration ships in a later release after app fully switched to new columns.


def downgrade() -> None:
    op.drop_constraint("ck_retention_churn_bps_range", "retention_cockpit")
    op.drop_constraint("ck_opportunities_value_amount_minor_nonneg", "opportunities")
    op.drop_column("retention_cockpit", "churn_probability_bps")
    op.drop_column("opportunities", "currency")
    op.drop_column("opportunities", "value_amount_minor")
