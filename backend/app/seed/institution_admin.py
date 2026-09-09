"""Creates the Institute Admin account for a freshly-provisioned tenant.

Mirrors `demo_institution.seed_demo_data`'s user-creation shape, but grants
"Institution Administrator" (unscoped) instead of "Super Administrator" —
the new role hierarchy starts here, not there — and sets
`must_change_password=True` since a real person, not a script, will sign in
with this account (same pattern as `program_roles.create_faculty`'s
new-faculty accounts).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import generate_temporary_password, hash_password
from app.models.tenant.identity import Role, User, UserRole


def create_institution_admin(db: Session, *, full_name: str, email: str) -> tuple[User, str]:
    """Create the tenant's first user, holding "Institution Administrator"
    unscoped. Returns the user and its generated temporary password (never
    persisted in plaintext — only the hash is stored)."""
    temporary_password = generate_temporary_password()
    admin = User(
        email=email,
        password_hash=hash_password(temporary_password),
        full_name=full_name,
        is_active=True,
        must_change_password=True,
    )
    db.add(admin)
    db.flush()

    role = db.query(Role).filter(Role.name == "Institution Administrator").one()
    db.add(UserRole(user_id=admin.id, role_id=role.id, scope_type=None, scope_id=None))

    return admin, temporary_password
