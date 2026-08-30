"""grade_submissions, attainment_snapshots (Faculty Module spec §21-24)

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def upgrade() -> None:
    op.create_table(
        "grade_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.course_sections.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(10), nullable=False, server_default="draft"),
        sa.Column(
            "submitted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
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

    op.create_table(
        "attainment_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "grade_submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.grade_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scope", sa.String(2), nullable=False),
        sa.Column(
            "course_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_outcomes.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "program_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("attainment_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("student_count", sa.Integer(), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_attainment_snapshots_grade_submission_id",
        "attainment_snapshots",
        ["grade_submission_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("attainment_snapshots", schema=_SCHEMA)
    op.drop_table("grade_submissions", schema=_SCHEMA)
