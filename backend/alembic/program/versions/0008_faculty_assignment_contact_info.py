"""faculty_assignments.{office_location,consultation_hours,meeting_link}
(Faculty Module spec §4.1 — the faculty-editable Course Settings fields)

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _program_schema() -> str:
    bind = op.get_bind()
    translate_map = bind.get_execution_options().get("schema_translate_map", {})
    program_schema = translate_map.get("program")
    if not program_schema:
        raise RuntimeError("program_schema not resolved — run with -x program_schema=...")
    return program_schema


def upgrade() -> None:
    schema = _program_schema()
    op.execute(
        sa.text(
            f'ALTER TABLE "{schema}".faculty_assignments ADD COLUMN office_location VARCHAR(255)'
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{schema}".faculty_assignments ADD COLUMN consultation_hours VARCHAR(255)'
        )
    )
    op.execute(
        sa.text(f'ALTER TABLE "{schema}".faculty_assignments ADD COLUMN meeting_link VARCHAR(500)')
    )


def downgrade() -> None:
    schema = _program_schema()
    op.execute(sa.text(f'ALTER TABLE "{schema}".faculty_assignments DROP COLUMN meeting_link'))
    op.execute(
        sa.text(f'ALTER TABLE "{schema}".faculty_assignments DROP COLUMN consultation_hours')
    )
    op.execute(sa.text(f'ALTER TABLE "{schema}".faculty_assignments DROP COLUMN office_location'))
