"""course_attainment_configs (attainment engine — app.models.tenant.assessments.marks)

Institution-shared (course_versions lives here too), fresh op.create_table
so schema_translate_map applies without the explicit schema= workaround —
see 0004_delivery_grading_assessment.py's docstring.

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-28 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "course_attainment_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_versions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("min_marks_percent", sa.Numeric(5, 2), nullable=False, server_default="60"),
        sa.Column("min_students_percent", sa.Numeric(5, 2), nullable=False, server_default="60"),
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
        "ix_course_attainment_configs_course_version_id",
        "course_attainment_configs",
        ["course_version_id"],
    )


def downgrade() -> None:
    op.drop_table("course_attainment_configs")
