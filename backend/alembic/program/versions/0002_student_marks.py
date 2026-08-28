"""student_marks (marks entry — app.models.tenant.assessments.marks)

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-28 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def upgrade() -> None:
    op.create_table(
        "student_marks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assessment_question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.assessment_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_enrollment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.student_enrollments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("marks_obtained", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "entered_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "entered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "assessment_question_id",
            "student_enrollment_id",
            name="uq_student_marks_question_enrollment",
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_student_marks_assessment_question_id",
        "student_marks",
        ["assessment_question_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_student_marks_student_enrollment_id",
        "student_marks",
        ["student_enrollment_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("student_marks", schema=_SCHEMA)
