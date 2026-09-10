"""program_versions.published_by/published_at/unpublished_by/unpublished_at/
previous_version_id (Master_Architecture_Part1.md §22-24)

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-08 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _schemas() -> tuple[str, str]:
    """op.add_column doesn't reliably honor schema_translate_map — see
    0006_assessment_document_deadline.py (tenant chain)."""
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
            f'ALTER TABLE "{program_schema}".program_versions '
            "ADD COLUMN published_by UUID "
            f'REFERENCES "{institution_schema}".users(id) ON DELETE SET NULL'
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions ADD COLUMN published_at TIMESTAMPTZ'
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions '
            "ADD COLUMN unpublished_by UUID "
            f'REFERENCES "{institution_schema}".users(id) ON DELETE SET NULL'
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions ADD COLUMN unpublished_at TIMESTAMPTZ'
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions '
            "ADD COLUMN previous_version_id UUID "
            f'REFERENCES "{program_schema}".program_versions(id) ON DELETE SET NULL'
        )
    )


def downgrade() -> None:
    _, program_schema = _schemas()
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions DROP COLUMN previous_version_id'
        )
    )
    op.execute(
        sa.text(f'ALTER TABLE "{program_schema}".program_versions DROP COLUMN unpublished_at')
    )
    op.execute(
        sa.text(f'ALTER TABLE "{program_schema}".program_versions DROP COLUMN unpublished_by')
    )
    op.execute(
        sa.text(f'ALTER TABLE "{program_schema}".program_versions DROP COLUMN published_at')
    )
    op.execute(
        sa.text(f'ALTER TABLE "{program_schema}".program_versions DROP COLUMN published_by')
    )
