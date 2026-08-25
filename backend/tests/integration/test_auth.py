"""End-to-end auth flow against a real provisioned tenant: login -> access
token -> /auth/me -> refresh, plus a require_permission()-gated endpoint
denying an under-permissioned user.

Requires a reachable PostgreSQL (`require_database` skips cleanly otherwise).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import session_scope
from app.main import app
from app.models.tenant.identity import Permission, Role, RolePermission, User, UserRole

pytestmark = pytest.mark.usefixtures("require_database")

_PASSWORD = "SuperSecret123!"  # noqa: S105 - test-only credential


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _tenant_headers(slug: str) -> dict[str, str]:
    return {settings.dev_tenant_header: slug}


def _create_user_with_permissions(schema_name: str, email: str, codes: list[str]) -> None:
    with session_scope(schema_translate_map={None: schema_name}) as db:
        user = User(email=email, password_hash=hash_password(_PASSWORD), full_name="Test User")
        db.add(user)
        db.flush()

        role = Role(name=f"role-for-{email}", description="test role", is_system_role=False)
        db.add(role)
        db.flush()

        for code in codes:
            permission = db.query(Permission).filter(Permission.code == code).one()
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        db.add(UserRole(user_id=user.id, role_id=role.id, scope_type=None, scope_id=None))


def test_login_me_refresh_flow(client: TestClient, provisioned_tenant) -> None:
    slug = provisioned_tenant.slug
    email = "flow-user@example.org"
    _create_user_with_permissions(provisioned_tenant.schema_name, email, ["org.view"])

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert login_resp.status_code == 200, login_resp.text
    tokens = login_resp.json()
    assert tokens["token_type"] == "bearer"
    access_token = tokens["access_token"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={**_tenant_headers(slug), "Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200, me_resp.text
    me = me_resp.json()
    assert me["email"] == email
    assert "org.view" in me["permissions"]

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
        headers=_tenant_headers(slug),
    )
    assert refresh_resp.status_code == 200, refresh_resp.text
    assert refresh_resp.json()["access_token"] != access_token


def test_login_rejects_wrong_password(client: TestClient, provisioned_tenant) -> None:
    slug = provisioned_tenant.slug
    email = "wrong-pw-user@example.org"
    _create_user_with_permissions(provisioned_tenant.schema_name, email, [])

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "not-the-password"},
        headers=_tenant_headers(slug),
    )
    assert resp.status_code == 401


def test_under_permissioned_user_is_denied_by_require_permission(
    client: TestClient, provisioned_tenant
) -> None:
    """User has org.view but not org.manage — creating a campus (which
    requires org.manage) must be rejected with 403, never silently allowed."""
    slug = provisioned_tenant.slug
    email = "view-only-user@example.org"
    _create_user_with_permissions(provisioned_tenant.schema_name, email, ["org.view"])

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _PASSWORD},
        headers=_tenant_headers(slug),
    )
    access_token = login_resp.json()["access_token"]

    create_resp = client.post(
        "/api/v1/org/campuses",
        json={"name": "Should Not Be Created", "code": "NOPE"},
        headers={**_tenant_headers(slug), "Authorization": f"Bearer {access_token}"},
    )
    assert create_resp.status_code == 403

    list_resp = client.get(
        "/api/v1/org/campuses",
        headers={**_tenant_headers(slug), "Authorization": f"Bearer {access_token}"},
    )
    assert list_resp.status_code == 200


def test_missing_token_is_unauthorized(client: TestClient, provisioned_tenant) -> None:
    resp = client.get("/api/v1/auth/me", headers=_tenant_headers(provisioned_tenant.slug))
    assert resp.status_code == 401


def test_unknown_institution_slug_is_not_found(
    client: TestClient, public_schema_ready: None
) -> None:
    resp = client.get("/api/v1/org/campuses", headers=_tenant_headers("does-not-exist"))
    assert resp.status_code == 404
