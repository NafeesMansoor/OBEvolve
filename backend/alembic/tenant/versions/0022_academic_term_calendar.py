"""academic_terms extended calendar fields (Master_Architecture_Part1.md §3)

Revision ID: 0022
Revises: 0021
Create Date: 2026-09-09 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = (
    "add_drop_last_date",
    "midterm_start_date",
    "midterm_end_date",
    "final_exam_start_date",
    "final_exam_end_date",
    "result_due_date",
    "result_publication_date",
)


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py's identical helper."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    for column in _COLUMNS:
        op.add_column(
            "academic_terms", sa.Column(column, sa.Date(), nullable=True), schema=schema
        )


def downgrade() -> None:
    schema = _target_schema()
    for column in reversed(_COLUMNS):
        op.drop_column("academic_terms", column, schema=schema)
