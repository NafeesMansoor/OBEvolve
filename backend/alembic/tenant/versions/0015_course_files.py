"""course_file_types, course_file_requirements (Faculty Module spec §5-9)

Institution-shared — fresh op.create_table so schema_translate_map applies
without the explicit schema= workaround (see 0010_course_attainment_config.py).

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-30 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "course_file_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column(
            "applicable_course_type", sa.String(10), nullable=False, server_default="both"
        ),
        sa.Column("is_custom", sa.Boolean(), nullable=False, server_default=sa.false()),
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
        sa.UniqueConstraint("key", name="uq_course_file_types_key"),
    )

    op.create_table(
        "course_file_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "academic_term_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_terms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_file_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_file_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("program_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("course_type", sa.String(10), nullable=True),
        sa.Column(
            "course_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_versions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("soft_copy_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hard_copy_required", sa.Boolean(), nullable=False, server_default=sa.false()),
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
    )
    op.create_index(
        "ix_course_file_requirements_academic_term_id",
        "course_file_requirements",
        ["academic_term_id"],
    )
    op.create_index(
        "ix_course_file_requirements_course_file_type_id",
        "course_file_requirements",
        ["course_file_type_id"],
    )
    op.create_index(
        "ix_course_file_requirements_course_version_id",
        "course_file_requirements",
        ["course_version_id"],
    )


def downgrade() -> None:
    op.drop_table("course_file_requirements")
    op.drop_table("course_file_types")
