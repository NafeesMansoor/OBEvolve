"""course_attainment_configs.wi_treatment (configurable W/I handling — spec §4)

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-28 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
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
        "course_attainment_configs",
        sa.Column("wi_treatment", sa.String(20), nullable=False, server_default="exclude"),
        schema=schema,
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_column("course_attainment_configs", "wi_treatment", schema=schema)
