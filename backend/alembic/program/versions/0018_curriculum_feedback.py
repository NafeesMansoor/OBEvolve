"""curriculum_feedback (Master_Architecture_Part1.md §25-26)

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-09 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def upgrade() -> None:
    op.create_table(
        "curriculum_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column(
            "submitted_by",
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
        "ix_curriculum_feedback_entity_type",
        "curriculum_feedback",
        ["entity_type"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_curriculum_feedback_entity_id", "curriculum_feedback", ["entity_id"], schema=_SCHEMA
    )
    op.create_index(
        "ix_curriculum_feedback_submitted_by",
        "curriculum_feedback",
        ["submitted_by"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("curriculum_feedback", schema=_SCHEMA)
