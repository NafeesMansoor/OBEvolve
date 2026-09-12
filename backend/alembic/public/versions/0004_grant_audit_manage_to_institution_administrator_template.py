"""Add `audit.manage` to the "Institution Administrator" role template.

New permission code (`app.core.permissions`), added to back the audit-log
retention/archiving setting (`GET/PATCH /audit/settings`, tenant
migration 0030). Same pattern as migration 0003's `institution.manage` add.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-12 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        sa.text(
            "SELECT permission_codes FROM role_templates WHERE name = 'Institution Administrator'"
        )
    ).fetchone()
    if row is None:
        return
    codes = list(row[0] or [])
    if "audit.manage" not in codes:
        codes.insert(codes.index("audit.view") + 1, "audit.manage")
        op.execute(
            sa.text(
                "UPDATE role_templates SET permission_codes = :codes "
                "WHERE name = 'Institution Administrator'"
            ).bindparams(sa.bindparam("codes", codes, type_=sa.JSON))
        )


def downgrade() -> None:
    bind = op.get_bind()
    row = bind.execute(
        sa.text(
            "SELECT permission_codes FROM role_templates WHERE name = 'Institution Administrator'"
        )
    ).fetchone()
    if row is None:
        return
    codes = [c for c in (row[0] or []) if c != "audit.manage"]
    op.execute(
        sa.text(
            "UPDATE role_templates SET permission_codes = :codes "
            "WHERE name = 'Institution Administrator'"
        ).bindparams(sa.bindparam("codes", codes, type_=sa.JSON))
    )
