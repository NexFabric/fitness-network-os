"""Add Wave 1 core gym models

Revision ID: c938894ffe0e
Revises: c938894ffe0d
Create Date: 2026-08-08 23:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.db.rls import disable_rls, enable_rls

# revision identifiers, used by Alembic.
revision: str = "c938894ffe0e"
down_revision: str | Sequence[str] | None = "c938894ffe0d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. locations
    op.create_table(
        "locations",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_locations_tenant_id"), "locations", ["tenant_id"], unique=False
    )
    enable_rls("locations")

    # 2. staff
    op.create_table(
        "staff",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("location_id", sa.Uuid(), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_staff_tenant_id"), "staff", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_staff_user_id"), "staff", ["user_id"], unique=False)
    enable_rls("staff")

    # 3. members
    op.create_table(
        "members",
        sa.Column("member_number", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_members_email"), "members", ["email"], unique=False)
    op.create_index(
        op.f("ix_members_member_number"), "members", ["member_number"], unique=False
    )
    op.create_index(op.f("ix_members_phone"), "members", ["phone"], unique=False)
    op.create_index(
        op.f("ix_members_tenant_id"), "members", ["tenant_id"], unique=False
    )
    enable_rls("members")

    # 4. member_tags
    op.create_table(
        "member_tags",
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_member_tags_tenant_id"), "member_tags", ["tenant_id"], unique=False
    )
    enable_rls("member_tags")

    # 5. member_notes
    op.create_table(
        "member_notes",
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_member_notes_tenant_id"), "member_notes", ["tenant_id"], unique=False
    )
    enable_rls("member_notes")

    # 6. consent_definitions
    op.create_table(
        "consent_definitions",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("consent_type", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_consent_definitions_tenant_id"),
        "consent_definitions",
        ["tenant_id"],
        unique=False,
    )
    enable_rls("consent_definitions")

    # 7. consent_versions
    op.create_table(
        "consent_versions",
        sa.Column("definition_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.String(), nullable=False),
        sa.Column("document_url", sa.String(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["definition_id"],
            ["consent_definitions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_consent_versions_tenant_id"),
        "consent_versions",
        ["tenant_id"],
        unique=False,
    )
    enable_rls("consent_versions")

    # 8. consent_records
    op.create_table(
        "consent_records",
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("consent_type", sa.String(), nullable=False),
        sa.Column("document_version", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("given_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_consent_records_tenant_id"),
        "consent_records",
        ["tenant_id"],
        unique=False,
    )
    enable_rls("consent_records")


def downgrade() -> None:
    disable_rls("consent_records")
    op.drop_index(op.f("ix_consent_records_tenant_id"), table_name="consent_records")
    op.drop_table("consent_records")

    disable_rls("consent_versions")
    op.drop_index(op.f("ix_consent_versions_tenant_id"), table_name="consent_versions")
    op.drop_table("consent_versions")

    disable_rls("consent_definitions")
    op.drop_index(
        op.f("ix_consent_definitions_tenant_id"), table_name="consent_definitions"
    )
    op.drop_table("consent_definitions")

    disable_rls("member_notes")
    op.drop_index(op.f("ix_member_notes_tenant_id"), table_name="member_notes")
    op.drop_table("member_notes")

    disable_rls("member_tags")
    op.drop_index(op.f("ix_member_tags_tenant_id"), table_name="member_tags")
    op.drop_table("member_tags")

    disable_rls("members")
    op.drop_index(op.f("ix_members_tenant_id"), table_name="members")
    op.drop_index(op.f("ix_members_phone"), table_name="members")
    op.drop_index(op.f("ix_members_member_number"), table_name="members")
    op.drop_index(op.f("ix_members_email"), table_name="members")
    op.drop_table("members")

    disable_rls("staff")
    op.drop_index(op.f("ix_staff_user_id"), table_name="staff")
    op.drop_index(op.f("ix_staff_tenant_id"), table_name="staff")
    op.drop_table("staff")

    disable_rls("locations")
    op.drop_index(op.f("ix_locations_tenant_id"), table_name="locations")
    op.drop_table("locations")
