"""Phase 11 CONTRACT (draft / deferred): drop legacy float columns

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2

STATUS: DEFERRED — do not apply until expand has shipped and app only uses
value_amount_minor / churn_probability_bps. Kept as sequential head placeholder
that is a no-op pass-through so chain stays linear; real DROP is gated.

Actually: we leave this migration as NO-OP with clear comments so alembic head
stays at expand-only until explicitly enabled. Operators enable DROP by replacing
this body in a follow-up PR after dual-column period.

For CI simplicity this revision is currently a documented no-op so head advances
and expand is the only active schema change. Contract DROP will be filled in
PR phase11-contract (or pre-phase12).
"""
from collections.abc import Sequence

revision: str = "g8b9c0d1e2f3"
down_revision: str | Sequence[str] | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Deferred contract. Intentionally empty.
    # When ready, replace with:
    #   op.drop_column("opportunities", "value")
    #   op.drop_column("retention_cockpit", "churn_probability")
    # and remove LEGACY_EXPAND_COLUMNS from alembic/env.py include_object.
    pass


def downgrade() -> None:
    pass
