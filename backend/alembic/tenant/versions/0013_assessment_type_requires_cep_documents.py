"""assessment_types.requires_cep_documents (Complex Engineering Problem
document set gate — spec §pending-review)

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-29 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
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
        sa.Column(
            "requires_cep_documents", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        schema=schema,
    )
    # Backfill for tenants that already had "Complex Engineering Problem"
    # seeded before this column existed — see 0012's identical backfill.
    table_name = f'"{schema}".assessment_types' if schema else "assessment_types"
    op.execute(
        sa.text(
            f"UPDATE {table_name} SET requires_cep_documents = true "
            "WHERE name = 'Complex Engineering Problem'"
        )
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_column("assessment_types", "requires_cep_documents", schema=schema)
