"""`POST /org/programs` (app.api.v1.endpoints.org.create_program) — exercised
through the real HTTP layer (TestClient), since the bug this guards against
lived entirely in the endpoint's transaction boundaries, not the service
layer `provision_program_schema` itself calls correctly either way.

Institute Settings feedback ("tried to add new program but failed to add
any") turned out to have two real, independent causes, both fixed here:

1. An invalid program code (anything outside `[a-z0-9-]` after lowercasing)
   raised `InvalidProgramCodeError`, which the endpoint didn't catch —
   surfaced as a raw unhandled 500 instead of a clear validation error.
2. Far more seriously: the endpoint used to call `provision_program_schema`
   *inside* its own still-open transaction (the just-inserted, unflushed-to-
   disk `Program` row). The new program schema's `program_versions` table
   carries a real FK back to that row, so creating it needs a lock the
   outer transaction already held — a genuine deadlock Postgres can't even
   detect (the outer session isn't blocked on any lock itself, just
   synchronously waiting in Python for the migration to finish), reproduced
   live while fixing bug #1: a stuck `idle in transaction` session next to
   a migration connection waiting on it, both stuck for 100+ minutes until
   manually killed. Fixed by committing the `Program` row *before*
   provisioning its schema, with an explicit compensating delete if
   provisioning then fails.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import session_scope
from app.main import app
from app.models.public.institution import Institution
from app.models.tenant.identity import Role, User, UserRole
from app.models.tenant.org import Campus, Department, Program, School

pytestmark = pytest.mark.usefixtures("require_database")

_PASSWORD = "SuperSecret123!"  # noqa: S105 - test-only credential


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _tenant_headers(slug: str) -> dict[str, str]:
    return {settings.dev_tenant_header: slug}


def _setup_admin_and_department(institution: Institution) -> str:
    """Institution Administrator + one department, ready for a program to
    be created under it. Returns the department id (as a string)."""
    with session_scope(schema_translate_map={None: institution.schema_name}) as db:
        user = User(
            email="admin@program-creation-test.example.org",
            password_hash=hash_password(_PASSWORD),
            full_name="Program Creation Test Admin",
        )
        db.add(user)
        db.flush()
        role = db.query(Role).filter(Role.name == "Institution Administrator").one()
        db.add(UserRole(user_id=user.id, role_id=role.id, scope_type=None, scope_id=None))

        campus = Campus(institution_id=institution.id, name="Main Campus", code="PCT")
        db.add(campus)
        db.flush()
        school = School(campus_id=campus.id, name="School of Eng", code="PCT")
        db.add(school)
        db.flush()
        department = Department(school_id=school.id, name="CSE", code="PCT")
        db.add(department)
        db.flush()
        return str(department.id)


def _login(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": _PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert resp.status_code == 200, resp.text
    return {**_tenant_headers(slug), "Authorization": f"Bearer {resp.json()['access_token']}"}


def test_creating_a_program_with_a_valid_code_provisions_its_schema(
    client: TestClient, provisioned_tenant: Institution, db_engine
) -> None:
    department_id = _setup_admin_and_department(provisioned_tenant)
    headers = _login(client, provisioned_tenant.slug, "admin@program-creation-test.example.org")

    resp = client.post(
        "/api/v1/org/programs",
        headers=headers,
        json={
            "department_id": department_id,
            "name": "Test Program",
            "code": "testprog",
            "degree_level": "BSc",
            "session_names": ["Fall", "Spring", "Summer"],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["code"] == "testprog"
    assert body["session_names"] == ["Fall", "Spring", "Summer"]

    program_schema = f"{provisioned_tenant.schema_name}__testprog"
    with db_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :s").bindparams(
                s=program_schema
            )
        ).scalar()
    assert exists, "program schema should have been created and migrated"

    with db_engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{program_schema}" CASCADE'))


def test_creating_a_program_with_an_invalid_code_is_rejected_and_not_stranded(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    department_id = _setup_admin_and_department(provisioned_tenant)
    headers = _login(client, provisioned_tenant.slug, "admin@program-creation-test.example.org")

    resp = client.post(
        "/api/v1/org/programs",
        headers=headers,
        json={
            "department_id": department_id,
            "name": "Bad Program",
            "code": "bad code!",
            "degree_level": None,
            "session_names": [],
        },
    )
    assert resp.status_code == 422, resp.text
    assert "only contain lowercase letters, digits, and hyphens" in resp.json()["detail"]

    # The compensating delete must actually have run — no stranded row left
    # behind by the rejected attempt (see module docstring bug #2).
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        assert db.query(Program).filter(Program.code == "bad code!").one_or_none() is None
