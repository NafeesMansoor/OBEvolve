"""initial program-schema tables (docs/adr/0003-schema-per-program.md)

Applied once per program schema via schema_translate_map — see
scripts/migrate_all_programs.py and app.services.tenancy.provision_program_schema.

Every table here is created with `schema="program"` (the marker key —
resolved to the real per-program schema, e.g. `tenant_ulab-cse__bscse`, by
env.py's schema_translate_map). FKs targeting another table in this same
chain use the `"program.<table>.id"` dotted form (NOT a bare
`"<table>.id"`) — SQLAlchemy does not infer a FK target's schema from the
referencing table's own schema, so an unqualified reference would resolve
against a phantom schema=None table instead of the real one. FKs targeting
an institution-shared table (`programs`, `academic_years`, `users`,
`course_versions`, `academic_terms`, `framework_pos`, `course_outcomes`,
`mapping_scale_levels`, `assessment_types`, `rubrics`, `questions`) are left
bare, resolved via the `None` translate-map key (the institution schema) —
both keys are active on the same connection during this migration run.

Revision ID: 0001
Revises:
Create Date: 2026-08-28 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def _timestamp_columns() -> tuple[sa.Column, sa.Column]:
    """Fresh `created_at`/`updated_at` Column objects (a Column can't be
    reused across multiple `create_table` calls)."""
    return (
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


def upgrade() -> None:
    # --- Curriculum (moved from the tenant chain's 0001) ---
    op.create_table(
        "program_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_label", sa.String(50), nullable=False),
        sa.Column(
            "effective_academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_years.id", ondelete="RESTRICT"),
            nullable=False,
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
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_versions_program_id",
        "program_versions",
        ["program_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_versions_effective_academic_year_id",
        "program_versions",
        ["effective_academic_year_id"],
        schema=_SCHEMA,
    )

    # --- OBE outcome hierarchy (moved from the tenant chain's 0002) ---
    op.create_table(
        "peos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_versions.id", ondelete="CASCADE"),
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
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_peos_program_version_id", "peos", ["program_version_id"], schema=_SCHEMA
    )

    op.create_table(
        "program_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_versions.id", ondelete="CASCADE"),
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
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_outcomes_program_version_id",
        "program_outcomes",
        ["program_version_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_outcomes_framework_po_id",
        "program_outcomes",
        ["framework_po_id"],
        schema=_SCHEMA,
    )

    # --- Course delivery (moved from the tenant chain's 0004) ---
    op.create_table(
        "course_offerings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "academic_term_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_terms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_offerings_course_version_id",
        "course_offerings",
        ["course_version_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_offerings_academic_term_id",
        "course_offerings",
        ["academic_term_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_offerings_program_version_id",
        "course_offerings",
        ["program_version_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "course_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_offering_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.course_offerings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_code", sa.String(20), nullable=False),
        sa.Column("max_students", sa.Integer(), nullable=True),
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_sections_course_offering_id",
        "course_sections",
        ["course_offering_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "faculty_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.course_sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "faculty_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_faculty_assignments_course_section_id",
        "faculty_assignments",
        ["course_section_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_faculty_assignments_faculty_user_id",
        "faculty_assignments",
        ["faculty_user_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "student_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.course_sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "enrollment_status", sa.String(20), nullable=False, server_default="enrolled"
        ),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_student_enrollments_student_user_id",
        "student_enrollments",
        ["student_user_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_student_enrollments_course_section_id",
        "student_enrollments",
        ["course_section_id"],
        schema=_SCHEMA,
    )

    # --- Mapping junctions (moved from the tenant chain's 0002) ---
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
            sa.ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mapping_scale_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_outcome_po_mappings_course_outcome_id",
        "course_outcome_po_mappings",
        ["course_outcome_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_outcome_po_mappings_program_outcome_id",
        "course_outcome_po_mappings",
        ["program_outcome_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_outcome_po_mappings_mapping_scale_level_id",
        "course_outcome_po_mappings",
        ["mapping_scale_level_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "program_outcome_peo_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "peo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.peos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mapping_scale_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_outcome_peo_mappings_program_outcome_id",
        "program_outcome_peo_mappings",
        ["program_outcome_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_outcome_peo_mappings_peo_id",
        "program_outcome_peo_mappings",
        ["peo_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_outcome_peo_mappings_mapping_scale_level_id",
        "program_outcome_peo_mappings",
        ["mapping_scale_level_id"],
        schema=_SCHEMA,
    )

    # --- Assessment instances (moved from the tenant chain's 0004) ---
    op.create_table(
        "assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.course_sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "academic_term_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_terms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessment_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("max_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("weight", sa.Numeric(5, 2), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "rubric_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rubrics.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_assessments_course_section_id", "assessments", ["course_section_id"], schema=_SCHEMA
    )
    op.create_index(
        "ix_assessments_academic_term_id", "assessments", ["academic_term_id"], schema=_SCHEMA
    )
    op.create_index(
        "ix_assessments_assessment_type_id",
        "assessments",
        ["assessment_type_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_assessments_rubric_id", "assessments", ["rubric_id"], schema=_SCHEMA
    )

    op.create_table(
        "assessment_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("marks_allocated", sa.Numeric(5, 2), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        *_timestamp_columns(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_assessment_questions_assessment_id",
        "assessment_questions",
        ["assessment_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_assessment_questions_question_id",
        "assessment_questions",
        ["question_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("assessment_questions", schema=_SCHEMA)
    op.drop_table("assessments", schema=_SCHEMA)
    op.drop_table("program_outcome_peo_mappings", schema=_SCHEMA)
    op.drop_table("course_outcome_po_mappings", schema=_SCHEMA)
    op.drop_table("student_enrollments", schema=_SCHEMA)
    op.drop_table("faculty_assignments", schema=_SCHEMA)
    op.drop_table("course_sections", schema=_SCHEMA)
    op.drop_table("course_offerings", schema=_SCHEMA)
    op.drop_table("program_outcomes", schema=_SCHEMA)
    op.drop_table("peos", schema=_SCHEMA)
    op.drop_table("program_versions", schema=_SCHEMA)
