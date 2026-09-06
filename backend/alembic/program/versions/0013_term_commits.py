"""term_commits (Final Commit: per-program, per-term lock on assessments/
marks/attainment writes)

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-05 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def upgrade() -> None:
    op.create_table(
        "term_commits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "academic_term_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_terms.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("is_committed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("manually_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "committed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
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
        "ix_term_commits_academic_term_id", "term_commits", ["academic_term_id"], schema=_SCHEMA
    )


def downgrade() -> None:
    op.drop_index("ix_term_commits_academic_term_id", table_name="term_commits", schema=_SCHEMA)
    op.drop_table("term_commits", schema=_SCHEMA)
