"""course_change_requests (Faculty Module spec §4.2)

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def upgrade() -> None:
    op.create_table(
        "course_change_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.course_sections.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_field", sa.String(30), nullable=False),
        sa.Column("current_value_json", postgresql.JSONB(), nullable=True),
        sa.Column("proposed_value_json", postgresql.JSONB(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("review_note", sa.Text(), nullable=True),
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
        "ix_course_change_requests_course_section_id",
        "course_change_requests",
        ["course_section_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_change_requests_requested_by",
        "course_change_requests",
        ["requested_by"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("course_change_requests", schema=_SCHEMA)
