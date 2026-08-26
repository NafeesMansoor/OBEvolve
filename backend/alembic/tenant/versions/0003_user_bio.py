"""users.bio (self-service profile)

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-27 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` (unlike `op.create_table`, used in
    0001/0002) do not reliably honor the connection's `schema_translate_map`
    — they fall through to the default schema instead of the tenant schema.
    Resolve it explicitly from the bind's execution options instead."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("bio", sa.Text(), nullable=True), schema=_target_schema()
    )


def downgrade() -> None:
    op.drop_column("users", "bio", schema=_target_schema())
