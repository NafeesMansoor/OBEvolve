"""courses.co_offered_with_id (self-referential, nullable)

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-28 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
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
        "courses",
        sa.Column("co_offered_with_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema=schema,
    )
    op.create_foreign_key(
        "fk_courses_co_offered_with_id",
        "courses",
        "courses",
        ["co_offered_with_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_courses_co_offered_with_id", "courses", ["co_offered_with_id"], schema=schema
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_index("ix_courses_co_offered_with_id", table_name="courses", schema=schema)
    op.drop_constraint(
        "fk_courses_co_offered_with_id", "courses", schema=schema, type_="foreignkey"
    )
    op.drop_column("courses", "co_offered_with_id", schema=schema)
