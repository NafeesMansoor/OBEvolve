"""Audit log archiving (Institute Settings feedback): a configurable
retention-days setting and a view-only "archived" filter — nothing is
physically moved (no background job runner exists in this app yet), logs
older than the retention window are just hidden from the default list view
and can be fetched back via a filter toggle. Adds:

1. A new `audit.manage` permission row (code added to
   `app.core.permissions` alongside this migration) and grants it to the
   existing "Institution Administrator" role, same as migration 0028 did
   for `institution.manage`.
2. `audit_log_settings`, a one-row-per-tenant table holding
   `retention_days` (nullable — unset means "never archive").

Revision ID: 0030
Revises: 0029
Create Date: 2026-09-12 00:00:00

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_AUDIT_MANAGE_DESCRIPTION = "Configure audit-log retention/archiving settings"


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column`/`op.create_table` don't reliably
    honor `schema_translate_map` — see 0003_user_bio.py."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""

    # 1. `audit.manage` permission row + grant to Institution Administrator.
    permission_id = uuid.uuid4()
    op.execute(
        sa.text(
            f"INSERT INTO {schema_prefix}permissions (id, code, description, module) "
            "VALUES (:id, 'audit.manage', :description, 'audit') "
            "ON CONFLICT (code) DO NOTHING"
        ).bindparams(id=permission_id, description=_AUDIT_MANAGE_DESCRIPTION)
    )
    op.execute(
        sa.text(
            f"INSERT INTO {schema_prefix}role_permissions (role_id, permission_id) "
            f"SELECT r.id, p.id FROM {schema_prefix}roles r, {schema_prefix}permissions p "
            "WHERE r.name = 'Institution Administrator' AND p.code = 'audit.manage' "
            "ON CONFLICT (role_id, permission_id) DO NOTHING"
        )
    )

    # 2. audit_log_settings (one row per tenant, created lazily by the
    # settings endpoint on first PATCH — no default row inserted here).
    op.create_table(
        "audit_log_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("retention_days", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        schema=schema,
    )


def downgrade() -> None:
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""
    op.drop_table("audit_log_settings", schema=schema)
    op.execute(
        sa.text(
            f"DELETE FROM {schema_prefix}role_permissions rp "
            f"USING {schema_prefix}roles r, {schema_prefix}permissions p "
            "WHERE rp.role_id = r.id AND rp.permission_id = p.id "
            "AND r.name = 'Institution Administrator' AND p.code = 'audit.manage'"
        )
    )
    op.execute(
        sa.text(f"DELETE FROM {schema_prefix}permissions WHERE code = 'audit.manage'")
    )
