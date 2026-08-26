"""course delivery, grading policy, assessment definition (Phase 4)

Applied once per tenant schema via schema_translate_map — see
scripts/migrate_all_tenants.py and app.services.tenancy.provision_tenant.
Every table here is a brand-new `op.create_table` (no ALTER involved), so
`schema_translate_map` applies without the explicit `schema=` workaround
0003 needed for `op.add_column` — see that migration's `_target_schema()`
docstring for why that workaround exists at all.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-27 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp_columns() -> tuple[sa.Column, sa.Column]:
    """Fresh `created_at`/`updated_at` Column objects (a Column can't be
    reused across multiple `create_table` calls) — factored out purely to
    keep each `create_table` call under the line-length limit."""
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
    # --- Course delivery (DATABASE_PLAN.md §C) ---
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
            sa.ForeignKey("program_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamp_columns(),
    )
    op.create_index(
        "ix_course_offerings_course_version_id", "course_offerings", ["course_version_id"]
    )
    op.create_index(
        "ix_course_offerings_academic_term_id", "course_offerings", ["academic_term_id"]
    )
    op.create_index(
        "ix_course_offerings_program_version_id", "course_offerings", ["program_version_id"]
    )

    op.create_table(
        "course_sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_offering_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_offerings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_code", sa.String(20), nullable=False),
        sa.Column("max_students", sa.Integer(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index(
        "ix_course_sections_course_offering_id", "course_sections", ["course_offering_id"]
    )

    op.create_table(
        "faculty_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_sections.id", ondelete="CASCADE"),
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
    )
    op.create_index(
        "ix_faculty_assignments_course_section_id", "faculty_assignments", ["course_section_id"]
    )
    op.create_index(
        "ix_faculty_assignments_faculty_user_id", "faculty_assignments", ["faculty_user_id"]
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
            sa.ForeignKey("course_sections.id", ondelete="CASCADE"),
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
    )
    op.create_index(
        "ix_student_enrollments_student_user_id", "student_enrollments", ["student_user_id"]
    )
    op.create_index(
        "ix_student_enrollments_course_section_id", "student_enrollments", ["course_section_id"]
    )

    # --- Grading policy (DATABASE_PLAN.md §C) ---
    op.create_table(
        "grading_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program_versions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index(
        "ix_grading_policies_program_version_id", "grading_policies", ["program_version_id"]
    )

    op.create_table(
        "grading_bands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "grading_policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("grading_policies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("letter_grade", sa.String(5), nullable=False),
        sa.Column("min_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("max_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("grade_point", sa.Numeric(3, 2), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        *_timestamp_columns(),
    )
    op.create_index("ix_grading_bands_grading_policy_id", "grading_bands", ["grading_policy_id"])

    # --- Assessment definition (DATABASE_PLAN.md §F) ---
    op.create_table(
        "assessment_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_custom", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        *_timestamp_columns(),
    )

    op.create_table(
        "rubrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_reusable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_timestamp_columns(),
    )

    op.create_table(
        "rubric_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rubric_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rubrics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("criterion", sa.Text(), nullable=False),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False),
        *_timestamp_columns(),
    )
    op.create_index("ix_rubric_criteria_rubric_id", "rubric_criteria", ["rubric_id"])

    op.create_table(
        "rubric_levels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rubric_criterion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rubric_criteria.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_index(
        "ix_rubric_levels_rubric_criterion_id", "rubric_levels", ["rubric_criterion_id"]
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(50), nullable=True),
        sa.Column("marks", sa.Numeric(5, 2), nullable=False),
        sa.Column("topic", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamp_columns(),
    )
    op.create_index("ix_questions_course_version_id", "questions", ["course_version_id"])
    op.create_index("ix_questions_author_id", "questions", ["author_id"])
    op.create_index("ix_questions_reviewer_id", "questions", ["reviewer_id"])

    op.create_table(
        "question_co_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_timestamp_columns(),
    )
    op.create_index(
        "ix_question_co_mappings_question_id", "question_co_mappings", ["question_id"]
    )
    op.create_index(
        "ix_question_co_mappings_course_outcome_id",
        "question_co_mappings",
        ["course_outcome_id"],
    )

    op.create_table(
        "question_bloom_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "bloom_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bloom_levels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_timestamp_columns(),
    )
    op.create_index(
        "ix_question_bloom_mappings_question_id", "question_bloom_mappings", ["question_id"]
    )
    op.create_index(
        "ix_question_bloom_mappings_bloom_level_id",
        "question_bloom_mappings",
        ["bloom_level_id"],
    )

    op.create_table(
        "assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_sections.id", ondelete="CASCADE"),
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
    )
    op.create_index("ix_assessments_course_section_id", "assessments", ["course_section_id"])
    op.create_index("ix_assessments_academic_term_id", "assessments", ["academic_term_id"])
    op.create_index("ix_assessments_assessment_type_id", "assessments", ["assessment_type_id"])
    op.create_index("ix_assessments_rubric_id", "assessments", ["rubric_id"])

    op.create_table(
        "assessment_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
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
    )
    op.create_index(
        "ix_assessment_questions_assessment_id", "assessment_questions", ["assessment_id"]
    )
    op.create_index(
        "ix_assessment_questions_question_id", "assessment_questions", ["question_id"]
    )


def downgrade() -> None:
    op.drop_table("assessment_questions")
    op.drop_table("assessments")
    op.drop_table("question_bloom_mappings")
    op.drop_table("question_co_mappings")
    op.drop_table("questions")
    op.drop_table("rubric_levels")
    op.drop_table("rubric_criteria")
    op.drop_table("rubrics")
    op.drop_table("assessment_types")
    op.drop_table("grading_bands")
    op.drop_table("grading_policies")
    op.drop_table("student_enrollments")
    op.drop_table("faculty_assignments")
    op.drop_table("course_sections")
    op.drop_table("course_offerings")
