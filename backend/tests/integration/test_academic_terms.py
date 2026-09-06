"""`POST /org/academic-terms/{id}/activate` — the single-active-term
invariant this endpoint exists to enforce (found live: `tenant_demo` had
two terms flagged `is_active=True` at once, silently polluting every
"current semester" view — see docs/course_level_settings_and_approval_workflow.md
§8/§11 and that endpoint's docstring). Uses the real HTTP layer
(`TestClient`), mirroring `test_auth.py`'s login pattern, since the bug this
guards against is specifically "does activating one term really deactivate
every other one," a real multi-row UPDATE behavior worth exercising through
the actual endpoint rather than the ORM directly.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import session_scope
from app.main import app
from app.models.tenant.identity import Permission, Role, RolePermission, User, UserRole
from app.models.tenant.org import AcademicTerm, AcademicYear

pytestmark = pytest.mark.usefixtures("require_database")

_PASSWORD = "SuperSecret123!"  # noqa: S105 - test-only credential


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _tenant_headers(slug: str) -> dict[str, str]:
    return {settings.dev_tenant_header: slug}


def _create_admin(schema_name: str, email: str) -> None:
    with session_scope(schema_translate_map={None: schema_name}) as db:
        user = User(email=email, password_hash=hash_password(_PASSWORD), full_name="Test Admin")
        db.add(user)
        db.flush()
        role = Role(name=f"role-for-{email}", description="test role", is_system_role=False)
        db.add(role)
        db.flush()
        permission = (
            db.query(Permission).filter(Permission.code == "academic_calendar.manage").one()
        )
        db.add(RolePermission(role_id=role.id, permission_id=permission.id))
        db.add(UserRole(user_id=user.id, role_id=role.id, scope_type=None, scope_id=None))


def _make_two_terms(schema_name: str) -> tuple[str, str]:
    with session_scope(schema_translate_map={None: schema_name}) as db:
        year = AcademicYear(label="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        db.add(year)
        db.flush()
        term_a = AcademicTerm(
            academic_year_id=year.id, name="Fall 2025", term_type="semester",
            start_date=date(2025, 9, 1), end_date=date(2025, 12, 20), is_active=True,
        )
        term_b = AcademicTerm(
            academic_year_id=year.id, name="Spring 2026", term_type="semester",
            start_date=date(2026, 1, 5), end_date=date(2026, 5, 15), is_active=True,
        )
        db.add_all([term_a, term_b])
        db.flush()
        return str(term_a.id), str(term_b.id)


def test_activating_a_term_deactivates_every_other_term(
    client: TestClient, provisioned_tenant
) -> None:
    slug = provisioned_tenant.slug
    email = "term-admin@example.org"
    _create_admin(provisioned_tenant.schema_name, email)
    term_a_id, term_b_id = _make_two_terms(provisioned_tenant.schema_name)

    login_resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": _PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert login_resp.status_code == 200, login_resp.text
    auth_headers = {
        **_tenant_headers(slug), "Authorization": f"Bearer {login_resp.json()['access_token']}",
    }

    # Both start active — the exact bug this fixes.
    listed = client.get("/api/v1/org/academic-terms", headers=auth_headers)
    assert sum(1 for t in listed.json() if t["is_active"]) == 2

    activate_resp = client.post(
        f"/api/v1/org/academic-terms/{term_b_id}/activate", headers=auth_headers
    )
    assert activate_resp.status_code == 200, activate_resp.text
    assert activate_resp.json()["is_active"] is True

    listed_after = {t["id"]: t["is_active"] for t in client.get(
        "/api/v1/org/academic-terms", headers=auth_headers
    ).json()}
    assert listed_after[term_b_id] is True
    assert listed_after[term_a_id] is False


def test_activate_requires_academic_calendar_manage_permission(
    client: TestClient, provisioned_tenant
) -> None:
    slug = provisioned_tenant.slug
    email = "no-permission-user@example.org"
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        db.add(User(email=email, password_hash=hash_password(_PASSWORD), full_name="No Perm"))
    term_a_id, _term_b_id = _make_two_terms(provisioned_tenant.schema_name)

    login_resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": _PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert login_resp.status_code == 200, login_resp.text
    auth_headers = {
        **_tenant_headers(slug), "Authorization": f"Bearer {login_resp.json()['access_token']}",
    }

    resp = client.post(f"/api/v1/org/academic-terms/{term_a_id}/activate", headers=auth_headers)
    assert resp.status_code == 403
