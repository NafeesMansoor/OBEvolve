"""course_file_submissions (Faculty Module spec §5-9)

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def upgrade() -> None:
    op.create_table(
        "course_file_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.course_sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_file_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_file_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("hard_copy_submitted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column(
            "submitted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
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
        sa.UniqueConstraint(
            "course_section_id", "course_file_type_id", name="uq_course_file_submission_slot"
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_file_submissions_course_section_id",
        "course_file_submissions",
        ["course_section_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_file_submissions_course_file_type_id",
        "course_file_submissions",
        ["course_file_type_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("course_file_submissions", schema=_SCHEMA)
