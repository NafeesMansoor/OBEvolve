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
    persisted in plaintext — only the hash is stored).

    Assumes `email` isn't already taken in this tenant — callers with an
    existing `users` table to worry about (unlike provisioning, which always
    starts from zero users) must check that themselves first, same as
    `program_roles.create_faculty` does."""
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


def list_institution_admins(db: Session) -> list[User]:
    """Every user currently holding "Institution Administrator" unscoped —
    used by the platform-admin "manage institution admins" surface (an
    institution can end up with zero, if it was provisioned without
    `admin_full_name`/`admin_email`, or more than one over time)."""
    role = db.query(Role).filter(Role.name == "Institution Administrator").one_or_none()
    if role is None:
        return []
    return (
        db.query(User)
        .join(UserRole, UserRole.user_id == User.id)
        .filter(UserRole.role_id == role.id, UserRole.scope_type.is_(None))
        .order_by(User.created_at)
        .all()
    )


def reset_institution_admin_password(db: Session, *, user: User) -> str:
    """Regenerate an existing Institution Administrator's password and force
    a change at next login — the platform-admin equivalent of `create_faculty`
    minting a new account, but for an admin who already exists. Returns the
    new one-time temporary password (never persisted in plaintext)."""
    temporary_password = generate_temporary_password()
    user.password_hash = hash_password(temporary_password)
    user.must_change_password = True
    db.add(user)
    return temporary_password
