"""roles.is_active

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-28 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """op.add_column()/op.drop_column() don't reliably honor the connection's
    schema_translate_map (see 0003_user_bio.py) — resolve explicitly."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    op.add_column(
        "roles",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        schema=_target_schema(),
    )


def downgrade() -> None:
    op.drop_column("roles", "is_active", schema=_target_schema())
