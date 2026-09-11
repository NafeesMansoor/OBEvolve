"""Rename role "Super Administrator" -> "Legacy Tenant Administrator".

The tenant-scoped role and the cross-institution `public.platform_admins`
account both ended up called "Super Administrator", which is confusing in
practice — they're unrelated accounts in unrelated schemas. The platform
account keeps the name (it's the one actually meant by it: Dr. Geek, the
entity that develops and maintains OBEvolve, sitting above every
institution). This tenant-scoped role — already disabled for new
assignment, existing holders unaffected — is renamed instead.

Same real `UPDATE` approach as 0025 (renaming "Course Coordinator" ->
"Section Coordinator"): `seed_default_roles`'s idempotency check is keyed by
`Role.name`, so just changing the seed name and re-running it would create a
brand-new "Legacy Tenant Administrator" role instead of renaming in place,
orphaning every existing "Super Administrator" grant.

Revision ID: 0027
Revises: 0026
Create Date: 2026-09-12 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
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
            f"UPDATE {schema_prefix}roles SET name = 'Legacy Tenant Administrator' "
            "WHERE name = 'Super Administrator'"
        )
    )


def downgrade() -> None:
    schema = _target_schema()
    schema_prefix = f'"{schema}".' if schema else ""
    op.execute(
        sa.text(
            f"UPDATE {schema_prefix}roles SET name = 'Super Administrator' "
            "WHERE name = 'Legacy Tenant Administrator'"
        )
    )
