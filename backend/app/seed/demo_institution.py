"""Seeds a demo institution's tenant schema with an admin user and a small
sample of organizational structure. Used by
`scripts/provision_tenant.py --seed-demo` and integration tests.

`bloom_levels` (DATABASE_PLAN.md §D) is a Phase 3 table that doesn't exist
in a Phase 1 tenant schema yet, so — per the "no fake/placeholder logic"
constraint — seeding it is skipped entirely here rather than faked.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.tenant.identity import Role, User, UserRole
from app.models.tenant.org import Campus, Department, Program, School

DEMO_ADMIN_EMAIL = "admin@demo.obevolve.dev"  # .local is a reserved/special-use
# TLD that pydantic's EmailStr (email-validator) rejects outright — see the
# LoginRequest schema. .dev is a real, non-reserved gTLD, safe for seed data
# that will actually be POSTed through email-validated endpoints.
DEMO_ADMIN_PASSWORD = "ChangeMe123!"  # noqa: S105 — demo-only seed credential, never used in prod


def seed_demo_data(
    db: Session,
    *,
    institution_id: uuid.UUID,
    admin_email: str = DEMO_ADMIN_EMAIL,
    admin_password: str = DEMO_ADMIN_PASSWORD,
) -> User:
    """Create one admin user + a Campus/School/Department/Program chain.

    Idempotent at the admin-user level: if `admin_email` already exists in
    this schema, returns that user without creating duplicate org structure.
    """
    existing = db.query(User).filter(User.email == admin_email).one_or_none()
    if existing is not None:
        return existing

    admin = User(
        email=admin_email,
        password_hash=hash_password(admin_password),
        full_name="Demo Institution Administrator",
        is_active=True,
    )
    db.add(admin)
    db.flush()

    super_admin_role = db.query(Role).filter(Role.name == "Super Administrator").one_or_none()
    if super_admin_role is not None:
        db.add(
            UserRole(user_id=admin.id, role_id=super_admin_role.id, scope_type=None, scope_id=None)
        )

    campus = Campus(institution_id=institution_id, name="Main Campus", code="MAIN")
    db.add(campus)
    db.flush()

    school = School(campus_id=campus.id, name="School of Engineering", code="ENG")
    db.add(school)
    db.flush()

    department = Department(
        school_id=school.id, name="Computer Science & Engineering", code="CSE"
    )
    db.add(department)
    db.flush()

    program = Program(
        department_id=department.id,
        name="B.Sc. in Computer Science & Engineering",
        code="BSCSE",
        degree_level="undergraduate",
    )
    db.add(program)
    db.flush()

    return admin
