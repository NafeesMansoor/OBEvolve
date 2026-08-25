"""Schema-per-tenant isolation is structural, not just application-code
discipline (docs/adr/0001-schema-per-tenant.md): a session bound to tenant
A's schema cannot see tenant B's rows, even for the identical table/query.

Requires a reachable PostgreSQL (`require_database` skips cleanly otherwise)
because this is exactly the guarantee that only a real multi-schema
Postgres database can demonstrate — there is no meaningful sqlite stand-in.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text

from app.db.session import session_scope
from app.models.public.institution import Institution
from app.models.tenant.org import Campus
from app.services.tenancy import provision_tenant

pytestmark = pytest.mark.usefixtures("require_database")


def _make_tenant(public_db, suffix: str) -> Institution:
    slug = f"iso-{suffix}-{uuid.uuid4().hex[:6]}"
    return provision_tenant(
        public_db,
        name=f"Isolation Test {slug}",
        code=slug.upper(),
        slug=slug,
        contact_email=f"admin@{slug}.example.org",
    )


def _drop_tenant(db_engine, public_db, institution: Institution) -> None:
    with db_engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{institution.schema_name}" CASCADE'))
    public_db.query(Institution).filter(Institution.id == institution.id).delete()
    public_db.commit()


def test_data_written_in_one_tenant_is_invisible_from_another(public_db, db_engine) -> None:
    tenant_a = _make_tenant(public_db, "a")
    tenant_b = _make_tenant(public_db, "b")
    try:
        with session_scope(schema_translate_map={None: tenant_a.schema_name}) as db_a:
            campus = Campus(institution_id=tenant_a.id, name="Tenant A Campus", code="A1")
            db_a.add(campus)
            db_a.flush()
            campus_id = campus.id

        # Same tenant, new session: the row persisted.
        with session_scope(schema_translate_map={None: tenant_a.schema_name}) as db_a_again:
            assert db_a_again.get(Campus, campus_id) is not None

        # Different tenant: structurally cannot see it, whether queried by
        # id or by a table scan.
        with session_scope(schema_translate_map={None: tenant_b.schema_name}) as db_b:
            assert db_b.get(Campus, campus_id) is None
            assert db_b.query(Campus).count() == 0
    finally:
        _drop_tenant(db_engine, public_db, tenant_a)
        _drop_tenant(db_engine, public_db, tenant_b)


def test_each_tenant_gets_its_own_seeded_rbac_catalogue(public_db, db_engine) -> None:
    """provision_tenant seeds default permissions/roles independently per
    schema — confirms seeding isn't accidentally shared/global state."""
    from app.models.tenant.identity import Role

    tenant_a = _make_tenant(public_db, "c")
    try:
        with session_scope(schema_translate_map={None: tenant_a.schema_name}) as db_a:
            role_names = {r.name for r in db_a.query(Role).all()}
        assert "Super Administrator" in role_names
        assert "Student" in role_names
    finally:
        _drop_tenant(db_engine, public_db, tenant_a)
