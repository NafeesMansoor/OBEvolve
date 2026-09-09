"""performance_indicators + program_versions.po_definition_method/
peo_numbering_style/po_numbering_style (Master_Architecture_Part1.md §12-13,
§18)

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-08 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


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
    _, program_schema = _schemas()

    op.create_table(
        "performance_indicators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_performance_indicators_program_outcome_id",
        "performance_indicators",
        ["program_outcome_id"],
        schema=_SCHEMA,
    )

    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions '
            "ADD COLUMN po_definition_method VARCHAR(20) NOT NULL DEFAULT 'direct'"
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions '
            "ADD COLUMN peo_numbering_style VARCHAR(20) NOT NULL DEFAULT 'numeric'"
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions '
            "ADD COLUMN po_numbering_style VARCHAR(20) NOT NULL DEFAULT 'numeric'"
        )
    )


def downgrade() -> None:
    _, program_schema = _schemas()
    op.execute(
        sa.text(f'ALTER TABLE "{program_schema}".program_versions DROP COLUMN po_numbering_style')
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions DROP COLUMN peo_numbering_style'
        )
    )
    op.execute(
        sa.text(
            f'ALTER TABLE "{program_schema}".program_versions DROP COLUMN po_definition_method'
        )
    )
    op.drop_table("performance_indicators", schema=_SCHEMA)
