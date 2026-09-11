"""Platform-admin institution-admin management (app.seed.institution_admin's
list/reset additions, exercised via the same tenant-schema session pattern
`institutions.py`'s new endpoints use) — an institution provisioned without
an admin can still get one assigned later, and an existing admin's password
can be reset without touching their role grant.

Requires a reachable PostgreSQL (`require_database` skips cleanly otherwise),
same reasoning as test_tenancy_isolation.py.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.db.session import session_scope
from app.models.public.institution import Institution
from app.models.tenant.identity import Role, User, UserRole
from app.seed.institution_admin import (
    create_institution_admin,
    list_institution_admins,
    reset_institution_admin_password,
)
from app.services.tenancy import provision_tenant

pytestmark = pytest.mark.usefixtures("require_database")


def _make_tenant_without_admin(public_db, suffix: str) -> Institution:
    slug = f"admin-mgmt-{suffix}-{uuid.uuid4().hex[:6]}"
    institution, admin_password = provision_tenant(
        public_db,
        name=f"Admin Management Test {slug}",
        code=slug.upper(),
        slug=slug,
        contact_email=f"admin@{slug}.example.org",
    )
    assert admin_password is None  # no admin_full_name/admin_email passed
    return institution


def _drop_tenant(db_engine, public_db, institution: Institution) -> None:
    with db_engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{institution.schema_name}" CASCADE'))
    public_db.query(Institution).filter(Institution.id == institution.id).delete()
    public_db.commit()


def test_institution_provisioned_without_admin_can_get_one_assigned_later(
    public_db, db_engine
) -> None:
    tenant = _make_tenant_without_admin(public_db, "a")
    try:
        with session_scope(schema_translate_map={None: tenant.schema_name}) as db:
            assert list_institution_admins(db) == []

            admin, temporary_password = create_institution_admin(
                db, full_name="Late Admin", email="late-admin@example.org"
            )
            assert temporary_password
            assert admin.must_change_password is True

        with session_scope(schema_translate_map={None: tenant.schema_name}) as db_again:
            admins = list_institution_admins(db_again)
            assert [a.email for a in admins] == ["late-admin@example.org"]

            role = db_again.query(Role).filter(Role.name == "Institution Administrator").one()
            grant = (
                db_again.query(UserRole)
                .filter(UserRole.user_id == admins[0].id, UserRole.role_id == role.id)
                .one()
            )
            assert grant.scope_type is None
    finally:
        _drop_tenant(db_engine, public_db, tenant)


def test_reset_institution_admin_password_rotates_password_keeps_role(
    public_db, db_engine
) -> None:
    tenant = _make_tenant_without_admin(public_db, "b")
    try:
        with session_scope(schema_translate_map={None: tenant.schema_name}) as db:
            admin, original_password = create_institution_admin(
                db, full_name="Reset Me", email="reset-me@example.org"
            )
            admin.must_change_password = False  # simulate: already changed it once
            db.add(admin)
            db.flush()
            admin_id = admin.id
            original_hash = admin.password_hash

        with session_scope(schema_translate_map={None: tenant.schema_name}) as db_reset:
            user = db_reset.get(User, admin_id)
            assert user is not None
            new_password = reset_institution_admin_password(db_reset, user=user)
            assert new_password != original_password

        with session_scope(schema_translate_map={None: tenant.schema_name}) as db_after:
            user_after = db_after.get(User, admin_id)
            assert user_after is not None
            assert user_after.password_hash != original_hash
            assert user_after.must_change_password is True

            admins = list_institution_admins(db_after)
            assert [a.email for a in admins] == ["reset-me@example.org"]
    finally:
        _drop_tenant(db_engine, public_db, tenant)
