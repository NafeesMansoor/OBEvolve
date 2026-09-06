"""course_types + courses.course_type_id (Course-Level Settings spec §1)

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-05 00:00:00

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    op.create_table(
        "course_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        schema=schema,
    )
    op.add_column(
        "courses",
        sa.Column("course_type_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema=schema,
    )
    op.create_index(
        "ix_courses_course_type_id", "courses", ["course_type_id"], schema=schema
    )
    op.create_foreign_key(
        "fk_courses_course_type_id",
        "courses",
        "course_types",
        ["course_type_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="SET NULL",
    )

    # Every course predates this feature and has no course_type_id yet, and
    # an unclassified course is treated as fully locked (see
    # app.services.course_type_config.ensure_section_enabled). Backfilling a
    # permissive default type — rather than leaving every existing course
    # locked the moment this migration runs — preserves today's actual
    # behavior (faculty can already edit all four sections directly); the
    # matching program migration (0012_course_type_section_configs) enables
    # all four sections for this same type. Institutions can later introduce
    # more restrictive types and reclassify specific courses onto them.
    schema_prefix = f'"{schema}".' if schema else ""
    default_type_id = uuid.uuid4()
    op.execute(
        sa.text(
            f"INSERT INTO {schema_prefix}course_types (id, name, description, is_active) "
            "VALUES (:id, 'General', "
            "'Default type auto-created for courses that existed before Course-Level "
            "Settings — all sections left enabled to match prior behavior.', true)"
        ).bindparams(id=default_type_id)
    )
    op.execute(
        sa.text(
            f"UPDATE {schema_prefix}courses SET course_type_id = :id WHERE course_type_id IS NULL"
        ).bindparams(id=default_type_id)
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_constraint("fk_courses_course_type_id", "courses", schema=schema, type_="foreignkey")
    op.drop_index("ix_courses_course_type_id", table_name="courses", schema=schema)
    op.drop_column("courses", "course_type_id", schema=schema)
    op.drop_table("course_types", schema=schema)
