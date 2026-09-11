"""Merge role "Course Administrator" into "Section Coordinator" (they'd grown
to cover the same real-world ground: administrative control over one
course's data). Unlike 0025's plain rename, both roles already exist with
their own grants, so this is a real merge, not a rename:

1. Give Section Coordinator every permission Course Administrator held that
   it doesn't already have (union of role_permissions).
2. Repoint every Course Administrator `user_roles` grant at Section
   Coordinator, skipping (then dropping) any that would duplicate a grant
   the same user already holds as Section Coordinator at the identical
   scope.
3. Delete Course Administrator's own role_permissions and the role row
   itself.

A no-op wherever "Course Administrator" doesn't exist (a tenant provisioned
after `app.seed.default_roles` dropped it never gets one).

Revision ID: 0026
Revises: 0025
Create Date: 2026-09-11 00:00:00

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The permission codes Course Administrator held before the merge (from
# app.seed.default_roles as of the revision this migration was written
# against) — used only to recreate the role on downgrade.
_COURSE_ADMINISTRATOR_PERMISSION_CODES: tuple[str, ...] = (
    "curriculum.view",
    "outcome.create",
    "outcome.approve",
    "mapping.create",
    "section.manage",
    "section.view",
    "student.view",
    "grading.view",
    "assessment.create",
    "assessment.approve",
    "assessment.view",
    "marks.enter",
    "raw_data.manage_scoped",
    "course_file.configure",
    "course_file.review",
    "course_file.view",
    "course_change_request.review",
    "course_change_request.review_admin",
)

_COURSE_ADMINISTRATOR_DESCRIPTION = (
    "Full administrative control over one course's data (typically scoped "
    "to one course via UserRole.scope_type='course') — the raw-data-console "
    "peer of Program Administrator, but scoped to a single course."
)


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""
    bind = op.get_bind()

    course_admin_id = bind.execute(
        sa.text(f"SELECT id FROM {schema_prefix}roles WHERE name = 'Course Administrator'")
    ).scalar()
    if course_admin_id is None:
        return

    section_coordinator_id = bind.execute(
        sa.text(f"SELECT id FROM {schema_prefix}roles WHERE name = 'Section Coordinator'")
    ).scalar()
    if section_coordinator_id is None:
        # Shouldn't happen (Section Coordinator is seeded for every tenant),
        # but bail rather than delete Course Administrator with nowhere for
        # its grants to go.
        return

    # 1. Union role_permissions.
    op.execute(
        sa.text(
            f"INSERT INTO {schema_prefix}role_permissions (role_id, permission_id) "
            f"SELECT :section_coordinator_id, permission_id "
            f"FROM {schema_prefix}role_permissions WHERE role_id = :course_admin_id "
            "ON CONFLICT (role_id, permission_id) DO NOTHING"
        ).bindparams(section_coordinator_id=section_coordinator_id, course_admin_id=course_admin_id)
    )

    # 2. Repoint user_roles grants, skipping ones that would duplicate an
    # existing Section Coordinator grant at the same (user, scope).
    op.execute(
        sa.text(
            f"UPDATE {schema_prefix}user_roles ur SET role_id = :section_coordinator_id "
            "WHERE ur.role_id = :course_admin_id "
            "AND NOT EXISTS ("
            f"  SELECT 1 FROM {schema_prefix}user_roles ur2 "
            "  WHERE ur2.role_id = :section_coordinator_id "
            "  AND ur2.user_id = ur.user_id "
            "  AND ur2.scope_type IS NOT DISTINCT FROM ur.scope_type "
            "  AND ur2.scope_id IS NOT DISTINCT FROM ur.scope_id"
            ")"
        ).bindparams(section_coordinator_id=section_coordinator_id, course_admin_id=course_admin_id)
    )
    # Drop the now-redundant duplicates left pointing at the old role.
    op.execute(
        sa.text(
            f"DELETE FROM {schema_prefix}user_roles WHERE role_id = :course_admin_id"
        ).bindparams(course_admin_id=course_admin_id)
    )

    # 3. Drop Course Administrator's own grants and the role itself.
    op.execute(
        sa.text(
            f"DELETE FROM {schema_prefix}role_permissions WHERE role_id = :course_admin_id"
        ).bindparams(course_admin_id=course_admin_id)
    )
    op.execute(
        sa.text(f"DELETE FROM {schema_prefix}roles WHERE id = :course_admin_id").bindparams(
            course_admin_id=course_admin_id
        )
    )


def downgrade() -> None:
    """Best-effort only: recreates the Course Administrator role with its
    original permission set. It cannot un-merge `user_roles` grants — any
    holder who was reassigned to Section Coordinator during upgrade() stays
    Section Coordinator, since which grants originated from which role is no
    longer recoverable once merged."""
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""
    bind = op.get_bind()

    already_exists = bind.execute(
        sa.text(f"SELECT 1 FROM {schema_prefix}roles WHERE name = 'Course Administrator'")
    ).scalar()
    if already_exists:
        return

    course_admin_id = uuid.uuid4()
    op.execute(
        sa.text(
            f"INSERT INTO {schema_prefix}roles "
            "(id, name, description, is_system_role, is_active) "
            "VALUES (:id, 'Course Administrator', :description, true, true)"
        ).bindparams(id=course_admin_id, description=_COURSE_ADMINISTRATOR_DESCRIPTION)
    )
    for code in _COURSE_ADMINISTRATOR_PERMISSION_CODES:
        op.execute(
            sa.text(
                f"INSERT INTO {schema_prefix}role_permissions (role_id, permission_id) "
                f"SELECT :course_admin_id, id FROM {schema_prefix}permissions WHERE code = :code "
                "ON CONFLICT (role_id, permission_id) DO NOTHING"
            ).bindparams(course_admin_id=course_admin_id, code=code)
        )
