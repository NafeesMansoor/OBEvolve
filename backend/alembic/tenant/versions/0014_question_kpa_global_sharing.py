"""questions.kpa, questions.is_globally_shared (Faculty Module spec §17-18)

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    op.add_column("questions", sa.Column("kpa", sa.String(1), nullable=True), schema=schema)
    op.add_column(
        "questions",
        sa.Column(
            "is_globally_shared", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        schema=schema,
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_column("questions", "is_globally_shared", schema=schema)
    op.drop_column("questions", "kpa", schema=schema)
