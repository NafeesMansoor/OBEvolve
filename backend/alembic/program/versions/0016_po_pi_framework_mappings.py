"""course_outcome_pi_mappings + po_knowledge_profile_mappings +
po_problem_attribute_mappings + po_engineering_activity_mappings
(Master_Architecture_Part1.md §17, §19, §21)

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-08 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"
_EXACTLY_ONE_TARGET = (
    "(program_outcome_id IS NOT NULL) != (performance_indicator_id IS NOT NULL)"
)


def _timestamps() -> list[sa.Column]:
    return [
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
    ]


def _dual_target_columns() -> list[sa.Column]:
    return [
        sa.Column(
            "program_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "performance_indicator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.performance_indicators.id", ondelete="CASCADE"),
            nullable=True,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "course_outcome_pi_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "performance_indicator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.performance_indicators.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mapping_scale_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_timestamps(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_outcome_pi_mappings_course_outcome_id",
        "course_outcome_pi_mappings",
        ["course_outcome_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_outcome_pi_mappings_performance_indicator_id",
        "course_outcome_pi_mappings",
        ["performance_indicator_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "po_knowledge_profile_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_dual_target_columns(),
        sa.Column(
            "knowledge_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "mapping_scale_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(_EXACTLY_ONE_TARGET, name="ck_po_kp_mapping_exactly_one_target"),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_kp_mappings_program_outcome_id",
        "po_knowledge_profile_mappings",
        ["program_outcome_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_kp_mappings_performance_indicator_id",
        "po_knowledge_profile_mappings",
        ["performance_indicator_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_kp_mappings_knowledge_profile_id",
        "po_knowledge_profile_mappings",
        ["knowledge_profile_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "po_problem_attribute_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_dual_target_columns(),
        sa.Column(
            "problem_attribute_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("problem_attributes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "mapping_scale_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(_EXACTLY_ONE_TARGET, name="ck_po_cep_mapping_exactly_one_target"),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_cep_mappings_program_outcome_id",
        "po_problem_attribute_mappings",
        ["program_outcome_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_cep_mappings_performance_indicator_id",
        "po_problem_attribute_mappings",
        ["performance_indicator_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_cep_mappings_problem_attribute_id",
        "po_problem_attribute_mappings",
        ["problem_attribute_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "po_engineering_activity_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        *_dual_target_columns(),
        sa.Column(
            "engineering_activity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("engineering_activities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "mapping_scale_level_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(_EXACTLY_ONE_TARGET, name="ck_po_cea_mapping_exactly_one_target"),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_cea_mappings_program_outcome_id",
        "po_engineering_activity_mappings",
        ["program_outcome_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_cea_mappings_performance_indicator_id",
        "po_engineering_activity_mappings",
        ["performance_indicator_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_po_cea_mappings_engineering_activity_id",
        "po_engineering_activity_mappings",
        ["engineering_activity_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("po_engineering_activity_mappings", schema=_SCHEMA)
    op.drop_table("po_problem_attribute_mappings", schema=_SCHEMA)
    op.drop_table("po_knowledge_profile_mappings", schema=_SCHEMA)
    op.drop_table("course_outcome_pi_mappings", schema=_SCHEMA)
