"""assessments.document_deadline_extended_* (Program Administrator can
extend the assessment-document upload deadline past the academic term's
end_date — spec §pending-review)

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-29 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _schemas() -> tuple[str, str]:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` for either the `None` key (see 0003_user_bio.py)
    or a named key like "program" (confirmed by hand: it literally tried
    `ALTER TABLE program.assessments`, a schema that doesn't exist) — so this
    migration uses raw `op.execute` with both resolved physical schema names
    instead."""
    bind = op.get_bind()
    translate_map = bind.get_execution_options().get("schema_translate_map", {})
    institution_schema = translate_map.get(None)
    program_schema = translate_map.get("program")
    if not institution_schema or not program_schema:
        raise RuntimeError(
            "institution_schema/program_schema not resolved — run with "
            "-x institution_schema=... -x program_schema=..."
        )
    return institution_schema, program_schema


def upgrade() -> None:
    institution_schema, program_schema = _schemas()
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".assessments '
            "ADD COLUMN document_deadline_extended_to DATE"
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".assessments '
            "ADD COLUMN document_deadline_extended_by UUID "
            f'REFERENCES "{institution_schema}".users(id) ON DELETE SET NULL'
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".assessments '
            "ADD COLUMN document_deadline_extended_at TIMESTAMPTZ"
        )
    )


def downgrade() -> None:
    _, program_schema = _schemas()
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".assessments '
            "DROP COLUMN document_deadline_extended_at"
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".assessments '
            "DROP COLUMN document_deadline_extended_by"
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".assessments '
            "DROP COLUMN document_deadline_extended_to"
        )
    )
