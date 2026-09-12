"""Grant `institution.manage` to the existing "Institution Administrator" role.

It already held `institution.view` but not `institution.manage`, so the
institution's own identity/campus details (`PATCH /org/institution`) could be
viewed but never edited by the role meant to own institution-level
configuration — an oversight caught while building out Institute Settings
edit flows. `app.seed.default_roles` and the `public.role_templates` catalogue
(migration 0002 of the public chain) are updated to grant it to every
*future* institution at provisioning time; this migration backfills it onto
every already-provisioned tenant.

Revision ID: 0028
Revises: 0027
Create Date: 2026-09-12 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""
    op.execute(
        sa.text(
            f"INSERT INTO {schema_prefix}role_permissions (role_id, permission_id) "
            f"SELECT r.id, p.id FROM {schema_prefix}roles r, {schema_prefix}permissions p "
            "WHERE r.name = 'Institution Administrator' AND p.code = 'institution.manage' "
            "ON CONFLICT (role_id, permission_id) DO NOTHING"
        )
    )


def downgrade() -> None:
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""
    op.execute(
        sa.text(
            f"DELETE FROM {schema_prefix}role_permissions rp "
            f"USING {schema_prefix}roles r, {schema_prefix}permissions p "
            "WHERE rp.role_id = r.id AND rp.permission_id = p.id "
            "AND r.name = 'Institution Administrator' AND p.code = 'institution.manage'"
        )
    )
