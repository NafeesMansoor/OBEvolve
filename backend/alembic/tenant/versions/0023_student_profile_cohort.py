"""student_profiles.cohort_id (Master_Architecture_Part1.md §5)

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-09 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py's identical helper."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    # No FK: `cohorts` is schema="program" and an institution can have more
    # than one program — same reasoning as this table's existing
    # `program_version_id` column (see its model docstring in identity.py).
    op.add_column(
        "student_profiles",
        sa.Column("cohort_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema=schema,
    )
    op.create_index(
        "ix_student_profiles_cohort_id", "student_profiles", ["cohort_id"], schema=schema
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_index("ix_student_profiles_cohort_id", table_name="student_profiles", schema=schema)
    op.drop_column("student_profiles", "cohort_id", schema=schema)
