"""program_missions, program_visions, institutional_vision_program_vision_mappings,
peo_vision_mappings (Master_Architecture_Part1.md §8-11)

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-08 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def _timestamps() -> list[sa.Column]:
    return [
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
    ]


def _schemas() -> tuple[str, str]:
    """See 0006_assessment_document_deadline.py (tenant chain) for why the
    resolved physical schema name — not the "program" translate-map key — is
    needed for a cross-schema FK's REFERENCES clause below."""
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
    institution_schema, _ = _schemas()

    op.create_table(
        "program_missions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_missions_program_version_id",
        "program_missions",
        ["program_version_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "program_visions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(20), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_timestamps(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_program_visions_program_version_id",
        "program_visions",
        ["program_version_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "institutional_vision_program_vision_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_vision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_visions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "institutional_vision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{institution_schema}.institutional_visions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_timestamps(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_ivpv_mappings_program_vision_id",
        "institutional_vision_program_vision_mappings",
        ["program_vision_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_ivpv_mappings_institutional_vision_id",
        "institutional_vision_program_vision_mappings",
        ["institutional_vision_id"],
        schema=_SCHEMA,
    )

    op.create_table(
        "peo_vision_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "peo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.peos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_vision_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.program_visions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        *_timestamps(),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_peo_vision_mappings_peo_id", "peo_vision_mappings", ["peo_id"], schema=_SCHEMA
    )
    op.create_index(
        "ix_peo_vision_mappings_program_vision_id",
        "peo_vision_mappings",
        ["program_vision_id"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("peo_vision_mappings", schema=_SCHEMA)
    op.drop_table("institutional_vision_program_vision_mappings", schema=_SCHEMA)
    op.drop_table("program_visions", schema=_SCHEMA)
    op.drop_table("program_missions", schema=_SCHEMA)
