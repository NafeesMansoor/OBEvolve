"""Loads the fixed permission catalogue (`app.core.permissions.PERMISSIONS`)
into a tenant schema's `permissions` table. Idempotent — safe to call
against a schema that already has some or all rows."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.permissions import PERMISSIONS
from app.models.tenant.identity import Permission


def seed_default_permissions(db: Session) -> dict[str, Permission]:
    """Insert any catalogue permissions missing from this schema.

    Returns a `code -> Permission` map (including pre-existing rows) for
    callers (`seed_default_roles`) that need to resolve codes to rows.
    """
    existing = {perm.code: perm for perm in db.query(Permission).all()}
    for definition in PERMISSIONS:
        if definition.code in existing:
            continue
        perm = Permission(
            code=definition.code,
            description=definition.description,
            module=definition.module,
        )
        db.add(perm)
        existing[definition.code] = perm
    db.flush()
    return existing
