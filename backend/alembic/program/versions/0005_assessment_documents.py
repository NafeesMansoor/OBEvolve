"""assessment_documents (question paper / moderation form / compliance form
uploads for assessments whose type requires them — spec §pending-review)

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-29 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def upgrade() -> None:
    op.create_table(
        "assessment_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("program.assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(30), nullable=False),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.Text, nullable=True),
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
        # No unique(assessment_id, document_type): some document_types are
        # singleton slots (enforced by the upload endpoint's upsert logic),
        # others are repeatable (e.g. marked_rubric_sample, project_report —
        # "at least N" requirements) — see AssessmentDocument's docstring.
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_assessment_documents_assessment_id",
        "assessment_documents",
        ["assessment_id"],
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_assessment_documents_status",
        "assessment_documents",
        ["status"],
        schema=_SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("assessment_documents", schema=_SCHEMA)
