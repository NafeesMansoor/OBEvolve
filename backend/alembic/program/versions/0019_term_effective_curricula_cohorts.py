"""term_effective_curricula, cohorts (Master_Architecture_Part1.md §4-5)

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-09 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


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


def upgrade() -> None:
    op.create_table(
        "term_effective_curricula",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "academic_term_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_terms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        *_timestamps(),
        sa.UniqueConstraint(
            "academic_term_id", "program_version_id", name="uq_term_effective_curricula"
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_term_effective_curricula_academic_term_id",
        "term_effective_curricula",
        ["academic_term_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_term_effective_curricula_program_version_id",
        "term_effective_curricula",
        ["program_version_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "cohorts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column(
            "intake_term_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_terms.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("intake_year", sa.Integer(), nullable=False),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        *_timestamps(),
        schema=_SCHEMA,
    )
    op.create_index("ix_cohorts_intake_term_id", "cohorts", ["intake_term_id"], schema=_SCHEMA)
    op.create_index(
        "ix_cohorts_program_version_id", "cohorts", ["program_version_id"], schema=_SCHEMA
    )


def downgrade() -> None:
    op.drop_table("cohorts", schema=_SCHEMA)
    op.drop_table("term_effective_curricula", schema=_SCHEMA)
