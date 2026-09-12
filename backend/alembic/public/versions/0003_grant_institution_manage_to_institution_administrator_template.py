"""Add `institution.manage` to the "Institution Administrator" role template.

It held `institution.view` but not `institution.manage`, so an institution's
own identity/campus details could be viewed but never edited by the role
meant to own institution-level configuration — caught while building out
Institute Settings edit flows. `app.seed.default_roles.DEFAULT_ROLES` is
updated alongside this so every future institution's freshly-provisioned
role picks it up too; tenant migration 0028 backfills already-provisioned
tenants' actual `role_permissions` rows (this table only drives what *new*
tenants get seeded with, per `provision_tenant`'s template-first read).

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-12 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
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
    if "institution.manage" not in codes:
        codes.insert(codes.index("institution.view") + 1, "institution.manage")
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
    codes = [c for c in (row[0] or []) if c != "institution.manage"]
    op.execute(
        sa.text(
            "UPDATE role_templates SET permission_codes = :codes "
            "WHERE name = 'Institution Administrator'"
        ).bindparams(sa.bindparam("codes", codes, type_=sa.JSON))
    )
