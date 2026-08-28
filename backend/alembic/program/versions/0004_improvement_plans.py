"""improvement_plans (CO-failure continuous-improvement workflow — spec §5)

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-28 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def upgrade() -> None:
    op.create_table(
        "improvement_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.course_sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("problem_observation", sa.Text, nullable=False),
        sa.Column("proposed_action", sa.String(50), nullable=False),
        sa.Column("proposed_action_detail", sa.Text, nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("expected_improvement", sa.Text, nullable=False),
        sa.Column(
            "implementation_term_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_terms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "responsible_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="proposed"),
        sa.Column("evidence", sa.Text, nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
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
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_improvement_plans_course_section_id",
        "improvement_plans",
        ["course_section_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_improvement_plans_course_outcome_id",
        "improvement_plans",
        ["course_outcome_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("improvement_plans", schema=_SCHEMA)
