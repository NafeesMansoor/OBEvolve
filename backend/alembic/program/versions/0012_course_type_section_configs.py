"""course_type_section_configs + course_change_requests staged-approval
columns (Course-Level Settings and Approval Workflow spec §2-§7)

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-05 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCHEMA = "program"


def _program_schema() -> str:
    """`op.add_column`/`op.alter_column`/`op.drop_column` don't reliably
    honor `schema_translate_map` — see 0008_faculty_assignment_contact_info.py."""
    bind = op.get_bind()
    translate_map = bind.get_execution_options().get("schema_translate_map", {})
    program_schema = translate_map.get("program")
    if not program_schema:
        raise RuntimeError("program_schema not resolved — run with -x program_schema=...")
    return program_schema


def upgrade() -> None:
    op.create_table(
        "course_type_section_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "course_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("course_types.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section_key", sa.String(20), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
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
        sa.UniqueConstraint(
            "course_type_id", "section_key", name="uq_course_type_section"
        ),
        schema=_SCHEMA,
    )
    op.create_index(
        "ix_course_type_section_configs_course_type_id",
        "course_type_section_configs",
        ["course_type_id"],
        schema=_SCHEMA,
    )

    # --- course_change_requests: multi-stage approval columns ---
    schema = _program_schema()
    # `users` is tenant-shared (the institution schema), not program-scoped —
    # unlike `t` below, these FK targets must NOT use `schema`.
    institution_schema = op.get_bind().get_execution_options().get("schema_translate_map", {}).get(
        None
    )
    t = f'"{schema}".course_change_requests'
    op.execute(sa.text(f"ALTER TABLE {t} ALTER COLUMN status TYPE VARCHAR(30)"))
    op.execute(
        sa.text(f"ALTER TABLE {t} ADD COLUMN section_key VARCHAR(20) NOT NULL DEFAULT 'settings'")
    )
    op.execute(sa.text(f"ALTER TABLE {t} ALTER COLUMN section_key DROP DEFAULT"))
    op.execute(
        sa.text(
            f"ALTER TABLE {t} ADD COLUMN program_coordinator_reviewed_by UUID "
            f'REFERENCES "{institution_schema}".users(id) ON DELETE SET NULL'
        )
    )
    op.execute(sa.text(f"ALTER TABLE {t} ADD COLUMN program_coordinator_review_note TEXT"))
    op.execute(
        sa.text(
            f"ALTER TABLE {t} ADD COLUMN program_coordinator_reviewed_at TIMESTAMPTZ"
        )
    )
    op.execute(sa.text(f"ALTER TABLE {t} ADD COLUMN edited_value_json JSONB"))
    op.execute(
        sa.text(
            f"ALTER TABLE {t} ADD COLUMN edited_by UUID "
            f'REFERENCES "{institution_schema}".users(id) ON DELETE SET NULL'
        )
    )
    op.execute(sa.text(f"ALTER TABLE {t} ADD COLUMN edited_at TIMESTAMPTZ"))
    op.execute(sa.text(f"ALTER TABLE {t} ADD COLUMN apply_status VARCHAR(10)"))
    op.execute(sa.text(f"ALTER TABLE {t} ADD COLUMN apply_error TEXT"))
    # Pre-existing rows predate the staged workflow — every one of them was
    # single-stage under the old shape, so "pending" maps to the new
    # "pending_admin" (still awaiting the same first-stage reviewer);
    # already-terminal statuses (approved/rejected) are untouched.
    op.execute(sa.text(f"UPDATE {t} SET status = 'pending_admin' WHERE status = 'pending'"))

    # Enable all four sections for the "General" course type the sibling
    # tenant migration (0019_course_types) backfilled every pre-existing
    # course onto — otherwise every already-offered course in this program
    # would come out of this migration fully locked (see that migration's
    # comment). New, more restrictive course types created after this point
    # start unenabled, as intended.
    bind = op.get_bind()
    general_type_id = bind.execute(
        sa.text(
            f'SELECT id FROM "{institution_schema}".course_types WHERE name = :name'
        ).bindparams(name="General")
    ).scalar()
    if general_type_id is not None:
        config_table = f'"{schema}".course_type_section_configs'
        for section_key in ("overview", "settings", "students", "assessments"):
            op.execute(
                sa.text(
                    f"INSERT INTO {config_table} (id, course_type_id, section_key, is_enabled) "
                    "VALUES (gen_random_uuid(), :course_type_id, :section_key, true) "
                    "ON CONFLICT (course_type_id, section_key) DO NOTHING"
                ).bindparams(course_type_id=general_type_id, section_key=section_key)
            )


def downgrade() -> None:
    schema = _program_schema()
    t = f'"{schema}".course_change_requests'
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN apply_error"))
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN apply_status"))
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN edited_at"))
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN edited_by"))
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN edited_value_json"))
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN program_coordinator_reviewed_at"))
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN program_coordinator_review_note"))
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN program_coordinator_reviewed_by"))
    op.execute(sa.text(f"ALTER TABLE {t} DROP COLUMN section_key"))
    op.execute(sa.text(f"UPDATE {t} SET status = 'pending' WHERE status = 'pending_admin'"))
    op.execute(sa.text(f"ALTER TABLE {t} ALTER COLUMN status TYPE VARCHAR(10)"))

    op.drop_index(
        "ix_course_type_section_configs_course_type_id",
        table_name="course_type_section_configs",
        schema=_SCHEMA,
    )
    op.drop_table("course_type_section_configs", schema=_SCHEMA)
