"""Rename role "Course Coordinator" -> "Section Coordinator" (role hierarchy
revamp: Institute Admin -> Program Admin -> Program Coordinator -> Section
Coordinator -> Faculty -> Student).

A real `UPDATE` on the existing row, not a `RoleDef` rename left to
`seed_default_roles` alone — that function's idempotency check is keyed by
`Role.name`, so simply changing the seed name and re-running it would create
a brand-new "Section Coordinator" role instead of renaming in place,
orphaning every existing "Course Coordinator" grant.

Revision ID: 0025
Revises: 0024
Create Date: 2026-09-10 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""
    op.execute(
        sa.text(
            f"UPDATE {schema_prefix}roles SET name = 'Section Coordinator' "
            "WHERE name = 'Course Coordinator'"
        )
    )


def downgrade() -> None:
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""
    op.execute(
        sa.text(
            f"UPDATE {schema_prefix}roles SET name = 'Course Coordinator' "
            "WHERE name = 'Section Coordinator'"
        )
    )
