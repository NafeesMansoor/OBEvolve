"""course_versions/course_outcomes syllabus content — objectives, TLA
items, learning materials, target assessment weights, per-CO delivery
methods/assessment tools (Faculty Module Course Settings restoration,
course outline §1/§1.2/§1.6/§1.7 — excludes §1.5's week-by-week plan)

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    op.add_column("course_versions", sa.Column("objectives", sa.Text(), nullable=True), schema=schema)
    op.add_column("course_versions", sa.Column("tla_items", sa.Text(), nullable=True), schema=schema)
    op.add_column(
        "course_versions", sa.Column("learning_materials", sa.Text(), nullable=True), schema=schema
    )
    op.add_column(
        "course_versions",
        sa.Column("target_assessment_weights", sa.Text(), nullable=True),
        schema=schema,
    )
    op.add_column(
        "course_outcomes", sa.Column("delivery_methods", sa.Text(), nullable=True), schema=schema
    )
    op.add_column(
        "course_outcomes", sa.Column("assessment_tools", sa.Text(), nullable=True), schema=schema
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_column("course_outcomes", "assessment_tools", schema=schema)
    op.drop_column("course_outcomes", "delivery_methods", schema=schema)
    op.drop_column("course_versions", "target_assessment_weights", schema=schema)
    op.drop_column("course_versions", "learning_materials", schema=schema)
    op.drop_column("course_versions", "tla_items", schema=schema)
    op.drop_column("course_versions", "objectives", schema=schema)
