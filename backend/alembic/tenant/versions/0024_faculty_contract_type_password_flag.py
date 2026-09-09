"""faculty_profiles.contract_type, users.must_change_password
(Master_Architecture_Part1.md §30/§37)

Revision ID: 0024
Revises: 0023
Create Date: 2026-09-10 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
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
        "faculty_profiles",
        sa.Column("contract_type", sa.String(20), nullable=True),
        schema=schema,
    )
    op.add_column(
        "users",
        sa.Column(
            "must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        schema=schema,
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_column("users", "must_change_password", schema=schema)
    op.drop_column("faculty_profiles", "contract_type", schema=schema)
