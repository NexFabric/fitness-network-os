import re

with open("backend/app/models/membership.py", "r") as f:
    content = f.read()

# PlanVersion
content = re.sub(
    r'(price_amount_minor: Mapped\[int\] = mapped_column\(Integer, nullable=False\))',
    r'\1\n    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")',
    content
)

# Membership
content = re.sub(
    r'(price_snapshot: Mapped\[int \| None\] = mapped_column\(Integer, nullable=True\))',
    r'\1\n    price_snapshot_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)',
    content
)
content = re.sub(
    r'(status: Mapped\[str\] = mapped_column\(String, nullable=False, default="ACTIVE"\))',
    r'scheduled_cancellation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)\n    \1',
    content
)

# MembershipFreeze
content = re.sub(
    r'(actual_end_date: Mapped\[datetime \| None\] = mapped_column\(DateTime\(timezone=True\), nullable=True\))',
    r'\1\n    previous_status: Mapped[str | None] = mapped_column(String, nullable=True)',
    content
)

# MembershipFreeze Table args
idx_code = """
    _model_table_args = (
        ForeignKeyConstraint(["tenant_id", "membership_id"], ["memberships.tenant_id", "memberships.id"]),
        Index("ix_active_freeze", "tenant_id", "membership_id", unique=True, postgresql_where="actual_end_date IS NULL"),
    )
"""
content = re.sub(
    r'_model_table_args = \(\n\s+ForeignKeyConstraint\(\["tenant_id", "membership_id"\], \["memberships.tenant_id", "memberships.id"\]\),\n\s+\)',
    idx_code.strip(),
    content
)

# Import Index
if 'from sqlalchemy import Boolean' in content and 'Index' not in content:
    content = content.replace('from sqlalchemy import Boolean', 'from sqlalchemy import Boolean, Index')


# MembershipRenewal
content = re.sub(
    r'(price_snapshot: Mapped\[int \| None\] = mapped_column\(Integer, nullable=True\))',
    r'\1\n    price_snapshot_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)',
    content
)

with open("backend/app/models/membership.py", "w") as f:
    f.write(content)
