"""course catalog, OBE outcome hierarchy, mappings, accreditation framework
catalogue (Phase 2/3)

Applied once per tenant schema via schema_translate_map — see
scripts/migrate_all_tenants.py and app.services.tenancy.provision_tenant.
Table creation here has no `schema=` argument (so schema_translate_map
applies) — nothing in this migration needs a cross-schema FK.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-26 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Accreditation framework catalogue (DATABASE_PLAN.md §D/§K) ---
    op.create_table(
        "accreditation_bodies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "accreditation_frameworks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "accreditation_body_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_bodies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_accreditation_frameworks_accreditation_body_id",
        "accreditation_frameworks",
        ["accreditation_body_id"],
    )

    op.create_table(
        "framework_pos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_framework_pos_framework_id", "framework_pos", ["framework_id"])

    op.create_table(
        "knowledge_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_knowledge_profiles_framework_id", "knowledge_profiles", ["framework_id"])

    op.create_table(
        "problem_attributes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_problem_attributes_framework_id", "problem_attributes", ["framework_id"])

    op.create_table(
        "engineering_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_engineering_activities_framework_id", "engineering_activities", ["framework_id"]
    )

    # --- OBE outcome hierarchy (DATABASE_PLAN.md §D) ---
    op.create_table(
        "bloom_levels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "peos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_peos_program_version_id", "peos", ["program_version_id"])

    op.create_table(
        "program_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "framework_po_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("framework_pos.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_program_outcomes_program_version_id", "program_outcomes", ["program_version_id"]
    )
    op.create_index(
        "ix_program_outcomes_framework_po_id", "program_outcomes", ["framework_po_id"]
    )

    # --- Course catalog (DATABASE_PLAN.md §C) ---
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("credits", sa.Numeric(4, 2), nullable=False),
        sa.Column("contact_hours", sa.Integer(), nullable=True),
        sa.Column("course_type", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_courses_department_id", "courses", ["department_id"])

    op.create_table(
        "course_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_label", sa.String(50), nullable=False),
        sa.Column(
            "effective_academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_years.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_course_versions_course_id", "course_versions", ["course_id"])
    op.create_index(
        "ix_course_versions_effective_academic_year_id",
        "course_versions",
        ["effective_academic_year_id"],
    )

    op.create_table(
        "course_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "bloom_target_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bloom_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_course_outcomes_course_version_id", "course_outcomes", ["course_version_id"]
    )
    op.create_index(
        "ix_course_outcomes_bloom_target_level_id", "course_outcomes", ["bloom_target_level_id"]
    )

    # --- Mappings (DATABASE_PLAN.md §E) ---
    op.create_table(
        "mapping_scales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "mapping_scale_levels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "mapping_scale_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scales.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(50), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_mapping_scale_levels_mapping_scale_id", "mapping_scale_levels", ["mapping_scale_id"]
    )

    op.create_table(
        "course_outcome_po_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mapping_scale_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_course_outcome_po_mappings_course_outcome_id",
        "course_outcome_po_mappings",
        ["course_outcome_id"],
    )
    op.create_index(
        "ix_course_outcome_po_mappings_program_outcome_id",
        "course_outcome_po_mappings",
        ["program_outcome_id"],
    )
    op.create_index(
        "ix_course_outcome_po_mappings_mapping_scale_level_id",
        "course_outcome_po_mappings",
        ["mapping_scale_level_id"],
    )

    op.create_table(
        "program_outcome_peo_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "peo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("peos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mapping_scale_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_program_outcome_peo_mappings_program_outcome_id",
        "program_outcome_peo_mappings",
        ["program_outcome_id"],
    )
    op.create_index(
        "ix_program_outcome_peo_mappings_peo_id", "program_outcome_peo_mappings", ["peo_id"]
    )
    op.create_index(
        "ix_program_outcome_peo_mappings_mapping_scale_level_id",
        "program_outcome_peo_mappings",
        ["mapping_scale_level_id"],
    )


def downgrade() -> None:
    op.drop_table("program_outcome_peo_mappings")
    op.drop_table("course_outcome_po_mappings")
    op.drop_table("mapping_scale_levels")
    op.drop_table("mapping_scales")
    op.drop_table("course_outcomes")
    op.drop_table("course_versions")
    op.drop_table("courses")
    op.drop_table("program_outcomes")
    op.drop_table("peos")
    op.drop_table("bloom_levels")
    op.drop_table("engineering_activities")
    op.drop_table("problem_attributes")
    op.drop_table("knowledge_profiles")
    op.drop_table("framework_pos")
    op.drop_table("accreditation_frameworks")
    op.drop_table("accreditation_bodies")
