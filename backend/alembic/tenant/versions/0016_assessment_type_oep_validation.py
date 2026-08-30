"""assessment_types.requires_oep_validation (Faculty Module spec §19)

Revision ID: 0016
Revises: 0015
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    op.add_column(
        "assessment_types",
        sa.Column(
            "requires_oep_validation", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        schema=_target_schema(),
    )


def downgrade() -> None:
    op.drop_column("assessment_types", "requires_oep_validation", schema=_target_schema())
