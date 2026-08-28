"""assessment_types.requires_documents (exam-office document upload gate — spec §pending-review)

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-29 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
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
        "assessment_types",
        sa.Column("requires_documents", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema=schema,
    )
    # Backfill for tenants that already had "Midterm"/"Final Exam" seeded
    # before this column existed — app.seed.assessment_defaults only sets
    # requires_documents on newly-inserted rows, so already-seeded rows in
    # existing tenant schemas need this one-time data fix. Matches
    # DOCUMENT_REQUIRED_TYPE_NAMES in app/seed/assessment_defaults.py.
    table_name = f'"{schema}".assessment_types' if schema else "assessment_types"
    op.execute(
        sa.text(
            f"UPDATE {table_name} SET requires_documents = true "
            "WHERE name IN ('Midterm', 'Final Exam')"
        )
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_column("assessment_types", "requires_documents", schema=schema)
