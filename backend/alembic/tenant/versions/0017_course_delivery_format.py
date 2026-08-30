"""courses.delivery_format — theory/lab, drives Course Files checklist
(Faculty Module spec §6-8)

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column(
            "delivery_format", sa.String(10), nullable=False, server_default="theory"
        ),
        schema=_target_schema(),
    )


def downgrade() -> None:
    op.drop_column("courses", "delivery_format", schema=_target_schema())
