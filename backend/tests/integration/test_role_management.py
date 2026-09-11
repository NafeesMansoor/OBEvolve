"""Institution-level custom role ("user type") CRUD (`POST /users/roles`,
extended `PATCH /users/roles/{id}`, `GET /users/permissions`) — added this
round to close the gap where an Institution Administrator could only assign
existing roles to users, never create a genuinely new one. Exercised through
the real HTTP layer (TestClient), mirroring test_program_roles.py's pattern,
since the interesting behavior (system-role protection, permission-code
validation) lives in the endpoint, not just the service layer.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import session_scope
from app.main import app
from app.models.public.institution import Institution
from app.models.tenant.identity import Role, User, UserRole

pytestmark = pytest.mark.usefixtures("require_database")

_PASSWORD = "SuperSecret123!"  # noqa: S105 - test-only credential


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _tenant_headers(slug: str) -> dict[str, str]:
    return {settings.dev_tenant_header: slug}


def _make_institution_admin(schema_name: str, email: str) -> None:
    with session_scope(schema_translate_map={None: schema_name}) as db:
        user = User(email=email, password_hash=hash_password(_PASSWORD), full_name="Admin Two")
        db.add(user)
        db.flush()
        role = db.query(Role).filter(Role.name == "Institution Administrator").one()
        db.add(UserRole(user_id=user.id, role_id=role.id, scope_type=None, scope_id=None))


def _login(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": _PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert resp.status_code == 200, resp.text
    return {**_tenant_headers(slug), "Authorization": f"Bearer {resp.json()['access_token']}"}


def test_institution_admin_can_create_and_edit_a_custom_role(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    _make_institution_admin(provisioned_tenant.schema_name, "admin2@example.org")
    headers = _login(client, provisioned_tenant.slug, "admin2@example.org")

    perms_resp = client.get("/api/v1/users/permissions", headers=headers)
    assert perms_resp.status_code == 200, perms_resp.text
    codes = {p["code"] for p in perms_resp.json()}
    assert "curriculum.view" in codes

    create_resp = client.post(
        "/api/v1/users/roles",
        headers=headers,
        json={
            "name": "Lab Coordinator",
            "description": "Manages lab sections",
            "permission_codes": ["curriculum.view", "section.view", "not-a-real-code"],
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    assert created["is_system_role"] is False
    # Unknown code silently dropped, valid ones kept.
    assert set(created["permission_codes"]) == {"curriculum.view", "section.view"}

    role_id = created["id"]
    update_resp = client.patch(
        f"/api/v1/users/roles/{role_id}",
        headers=headers,
        json={"name": "Laboratory Coordinator", "permission_codes": ["curriculum.view"]},
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["name"] == "Laboratory Coordinator"
    assert updated["permission_codes"] == ["curriculum.view"]

    dup_resp = client.post(
        "/api/v1/users/roles",
        headers=headers,
        json={"name": "Laboratory Coordinator", "permission_codes": []},
    )
    assert dup_resp.status_code == 409


def test_system_role_name_and_permissions_cannot_be_edited(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    _make_institution_admin(provisioned_tenant.schema_name, "admin3@example.org")
    headers = _login(client, provisioned_tenant.slug, "admin3@example.org")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        faculty_role_id = str(db.query(Role).filter(Role.name == "Faculty").one().id)

    # is_active/description remain editable on a system role.
    ok_resp = client.patch(
        f"/api/v1/users/roles/{faculty_role_id}",
        headers=headers,
        json={"description": "Delivers courses (updated)"},
    )
    assert ok_resp.status_code == 200, ok_resp.text

    # name/permission_codes are not.
    blocked_resp = client.patch(
        f"/api/v1/users/roles/{faculty_role_id}",
        headers=headers,
        json={"name": "Renamed Faculty"},
    )
    assert blocked_resp.status_code == 403

    blocked_resp_2 = client.patch(
        f"/api/v1/users/roles/{faculty_role_id}",
        headers=headers,
        json={"permission_codes": ["curriculum.view"]},
    )
    assert blocked_resp_2.status_code == 403
