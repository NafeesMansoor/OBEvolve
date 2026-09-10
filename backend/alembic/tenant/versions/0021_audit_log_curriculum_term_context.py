"""audit_logs.academic_term_id/program_version_id
(Master_Architecture_Part1.md §44)

Revision ID: 0021
Revises: 0020
Create Date: 2026-09-08 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py's identical helper."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    op.add_column(
        "audit_logs",
        sa.Column("academic_term_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema=schema,
    )
    op.create_foreign_key(
        "fk_audit_logs_academic_term_id",
        "audit_logs",
        "academic_terms",
        ["academic_term_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_audit_logs_academic_term_id", "audit_logs", ["academic_term_id"], schema=schema
    )

    # No FK: program_versions lives in a per-program schema, and one
    # institution can have more than one program — same reasoning as
    # `StudentProfile.program_version_id` (identity.py).
    op.add_column(
        "audit_logs",
        sa.Column("program_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema=schema,
    )
    op.create_index(
        "ix_audit_logs_program_version_id", "audit_logs", ["program_version_id"], schema=schema
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_index("ix_audit_logs_program_version_id", table_name="audit_logs", schema=schema)
    op.drop_column("audit_logs", "program_version_id", schema=schema)
    op.drop_index("ix_audit_logs_academic_term_id", table_name="audit_logs", schema=schema)
    op.drop_constraint(
        "fk_audit_logs_academic_term_id", "audit_logs", schema=schema, type_="foreignkey"
    )
    op.drop_column("audit_logs", "academic_term_id", schema=schema)
