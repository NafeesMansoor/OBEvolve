"""assessments.purpose + assessment_question_po_mappings (Faculty Module
spec §18-19: CEP/OEP problem statement + CEP task-to-PO mapping)

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def _schemas() -> tuple[str, str]:
    """op.add_column doesn't reliably honor schema_translate_map — see
    0006_assessment_document_deadline.py."""
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
    op.execute(
        sa.text(f'ALTER TABLE "{program_schema}".assessments ADD COLUMN purpose TEXT')
    )

    op.create_table(
        "assessment_question_po_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assessment_question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.assessment_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_outcome_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
            nullable=False,
        ),
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
        "ix_assessment_question_po_mappings_assessment_question_id",
        "assessment_question_po_mappings",
        ["assessment_question_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_assessment_question_po_mappings_program_outcome_id",
        "assessment_question_po_mappings",
        ["program_outcome_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("assessment_question_po_mappings", schema=_SCHEMA)
    _, program_schema = _schemas()
    op.execute(sa.text(f'ALTER TABLE "{program_schema}".assessments DROP COLUMN purpose'))
