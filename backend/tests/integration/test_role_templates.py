"""`public.role_templates` — the platform-editable default "user type"
catalogue (`app/api/v1/endpoints/role_templates.py`), and its consumption by
`provision_tenant` (a fresh tenant's seeded roles should mirror whatever's
in this table, not just the hardcoded `DEFAULT_ROLES` constant). Exercised
through the real HTTP layer for the CRUD surface, and directly through
`provision_tenant` for the provisioning fallback, mirroring
test_role_management.py's and test_tenancy_isolation.py's patterns
respectively.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.security import hash_password
from app.db.session import session_scope
from app.main import app
from app.models.public.institution import Institution
from app.models.public.platform_admin import PlatformAdmin
from app.models.tenant.identity import Role, RolePermission
from app.services.tenancy import provision_tenant

pytestmark = pytest.mark.usefixtures("require_database")

_PASSWORD = "SuperSecret123!"  # noqa: S105 - test-only credential


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _make_platform_admin(public_db, email: str) -> None:
    public_db.add(
        PlatformAdmin(email=email, password_hash=hash_password(_PASSWORD), full_name="Platform Two")
    )
    public_db.commit()


def _login(client: TestClient, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/platform-auth/login", json={"email": email, "password": _PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_platform_admin_crud_on_role_templates(client: TestClient, public_db) -> None:
    from app.models.public.role_template import RoleTemplate

    _make_platform_admin(public_db, "platform2@example.org")
    headers = _login(client, "platform2@example.org")

    try:
        create_resp = client.post(
            "/api/v1/role-templates",
            headers=headers,
            json={
                "name": "Lab Coordinator",
                "description": "Manages lab sections",
                "permission_codes": ["curriculum.view", "not-a-real-code"],
            },
        )
        assert create_resp.status_code == 422, create_resp.text  # unknown code rejected outright

        ok_resp = client.post(
            "/api/v1/role-templates",
            headers=headers,
            json={
                "name": "Lab Coordinator",
                "description": "Manages lab sections",
                "permission_codes": ["curriculum.view", "section.view"],
            },
        )
        assert ok_resp.status_code == 201, ok_resp.text
        template_id = ok_resp.json()["id"]

        list_resp = client.get("/api/v1/role-templates", headers=headers)
        assert list_resp.status_code == 200
        assert any(t["name"] == "Lab Coordinator" for t in list_resp.json())

        update_resp = client.patch(
            f"/api/v1/role-templates/{template_id}",
            headers=headers,
            json={"is_active": False},
        )
        assert update_resp.status_code == 200, update_resp.text
        assert update_resp.json()["is_active"] is False

        delete_resp = client.delete(f"/api/v1/role-templates/{template_id}", headers=headers)
        assert delete_resp.status_code == 204, delete_resp.text

        list_after_delete = client.get("/api/v1/role-templates", headers=headers)
        assert not any(t["name"] == "Lab Coordinator" for t in list_after_delete.json())

        redelete_resp = client.delete(f"/api/v1/role-templates/{template_id}", headers=headers)
        assert redelete_resp.status_code == 404
    finally:
        # The endpoint requests commit through their own session (get_public_db,
        # not the `public_db` fixture), so this test's writes survive the
        # fixture's rollback-based teardown — clean them up explicitly, same
        # as provision_tenant-based tests do for the rows they commit.
        public_db.query(RoleTemplate).filter(RoleTemplate.name == "Lab Coordinator").delete()
        public_db.query(PlatformAdmin).filter(
            PlatformAdmin.email == "platform2@example.org"
        ).delete()
        public_db.commit()


def test_provision_tenant_seeds_roles_from_role_templates_when_present(
    public_db, db_engine
) -> None:
    """A role_templates row not present in the hardcoded DEFAULT_ROLES
    constant should still end up in a freshly-provisioned tenant's `roles`
    table — proving provision_tenant actually reads the live table rather
    than silently continuing to use the Python constant."""
    from app.models.public.role_template import RoleTemplate

    marker_name = f"Marker Role {uuid.uuid4().hex[:6]}"
    public_db.add(
        RoleTemplate(
            name=marker_name,
            description="Exists only to prove provisioning reads role_templates.",
            permission_codes=["curriculum.view"],
            all_permissions=False,
            is_active=True,
        )
    )
    public_db.commit()

    slug = f"role-tpl-{uuid.uuid4().hex[:8]}"
    institution, _ = provision_tenant(
        public_db,
        name=f"Role Template Test {slug}",
        code=slug.upper(),
        slug=slug,
        contact_email=f"admin@{slug}.example.org",
    )
    try:
        with session_scope(schema_translate_map={None: institution.schema_name}) as db:
            role = db.query(Role).filter(Role.name == marker_name).one_or_none()
            assert role is not None
            assert role.permission_codes == ["curriculum.view"]
    finally:
        with db_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{institution.schema_name}" CASCADE'))
        public_db.query(Institution).filter(Institution.id == institution.id).delete()
        public_db.query(RoleTemplate).filter(RoleTemplate.name == marker_name).delete()
        public_db.commit()


def test_resync_pushes_a_new_template_to_an_already_provisioned_tenant(
    client: TestClient, public_db, db_engine
) -> None:
    """A template created AFTER a tenant already exists has no effect on
    that tenant until POST /role-templates/resync is called — this is the
    propagation gap provision_tenant's one-time read leaves open."""
    from app.models.public.role_template import RoleTemplate

    slug = f"resync-{uuid.uuid4().hex[:8]}"
    institution, _ = provision_tenant(
        public_db,
        name=f"Resync Test {slug}",
        code=slug.upper(),
        slug=slug,
        contact_email=f"admin@{slug}.example.org",
    )
    marker_name = f"Late Role {uuid.uuid4().hex[:6]}"
    _make_platform_admin(public_db, "platform3@example.org")
    headers = _login(client, "platform3@example.org")

    try:
        with session_scope(schema_translate_map={None: institution.schema_name}) as db:
            assert db.query(Role).filter(Role.name == marker_name).one_or_none() is None

        create_resp = client.post(
            "/api/v1/role-templates",
            headers=headers,
            json={"name": marker_name, "permission_codes": ["curriculum.view"]},
        )
        assert create_resp.status_code == 201, create_resp.text

        with session_scope(schema_translate_map={None: institution.schema_name}) as db:
            assert db.query(Role).filter(Role.name == marker_name).one_or_none() is None

        resync_resp = client.post("/api/v1/role-templates/resync", headers=headers)
        assert resync_resp.status_code == 200, resync_resp.text
        body = resync_resp.json()
        # Only assert on this test's own institution — /resync loops every
        # institution in public.institutions, and a shared dev database can
        # accumulate unrelated stale institution rows (dropped schema, row
        # never cleaned up) whose failure here isn't this test's concern.
        assert institution.slug in body["succeeded"]
        assert institution.slug not in body["failed"]

        with session_scope(schema_translate_map={None: institution.schema_name}) as db:
            role = db.query(Role).filter(Role.name == marker_name).one_or_none()
            assert role is not None
            assert role.permission_codes == ["curriculum.view"]
    finally:
        # The /resync endpoint deliberately loops EVERY institution (same
        # all-tenants design as scripts/migrate_all_tenants.py), so it just
        # planted `marker_name` into every other real institution's `roles`
        # table too (e.g. local dev's "demo"/"ulab-cse") — clean those up as
        # well, not just the throwaway tenant this test created, or this
        # test would leave permanent stray roles behind everywhere.
        with session_scope() as cleanup_public_db:
            all_schemas = [
                inst.schema_name for inst in cleanup_public_db.query(Institution).all()
            ]
        for schema_name in all_schemas:
            # A stale/orphaned institution row (schema already dropped, row
            # never cleaned up) must not abort this loop before it reaches
            # the rest of this test's own cleanup below.
            try:
                with session_scope(schema_translate_map={None: schema_name}) as tdb:
                    role = tdb.query(Role).filter(Role.name == marker_name).one_or_none()
                    if role is not None:
                        tdb.query(RolePermission).filter(
                            RolePermission.role_id == role.id
                        ).delete()
                        tdb.delete(role)
            except Exception:
                continue

        with db_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{institution.schema_name}" CASCADE'))
        public_db.query(Institution).filter(Institution.id == institution.id).delete()
        public_db.query(RoleTemplate).filter(RoleTemplate.name == marker_name).delete()
        public_db.query(PlatformAdmin).filter(
            PlatformAdmin.email == "platform3@example.org"
        ).delete()
        public_db.commit()
