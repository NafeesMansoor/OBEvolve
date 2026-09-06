"""`app.api.v1.endpoints.program_roles` — the scoped surface that lets a
Program Coordinator/Administrator grant Faculty/Course Coordinator/Course
Administrator roles within their own program, without the privilege-
escalation risk of just adding `scope_type="program"` to the
institution-wide `role.manage` endpoints (see that module's docstring for
why). The whole point of these tests is verifying the escalation paths are
actually closed: granting a non-allowlisted role, granting a course from
another program, and revoking a grant that belongs to another program or is
institution-wide must all be rejected — exercised through the real HTTP
layer (`TestClient`), mirroring `test_auth.py`'s and `test_academic_terms.py`'s
pattern, since this is fundamentally about what the endpoint actually does
under a real request, not an isolated unit.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import session_scope
from app.main import app
from app.models.public.institution import Institution
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering
from app.models.tenant.identity import Permission, Role, RolePermission, User, UserRole
from app.models.tenant.org import AcademicTerm, AcademicYear, Campus, Department, Program, School
from app.services.tenancy import provision_program_schema

pytestmark = pytest.mark.usefixtures("require_database")

_PASSWORD = "SuperSecret123!"  # noqa: S105 - test-only credential


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _tenant_headers(slug: str) -> dict[str, str]:
    return {settings.dev_tenant_header: slug}


def _setup_two_programs(institution: Institution) -> dict[str, object]:
    """Program A (with one course/offering) and Program B (with a
    different course/offering) — used to prove a Program A coordinator
    cannot reach anything scoped to Program B."""
    with session_scope(schema_translate_map={None: institution.schema_name}) as db:
        campus = Campus(institution_id=institution.id, name="Main Campus", code="PRA")
        db.add(campus)
        db.flush()
        school = School(campus_id=campus.id, name="School of Eng", code="PRA")
        db.add(school)
        db.flush()
        department = Department(school_id=school.id, name="CSE", code="PRA")
        db.add(department)
        db.flush()

        program_a = Program(department_id=department.id, name="Program A", code="pra")
        program_b = Program(department_id=department.id, name="Program B", code="prb")
        db.add_all([program_a, program_b])
        db.flush()
        program_a_id, program_b_id = program_a.id, program_b.id

        course_a = Course(department_id=department.id, code="CA101", title="Course A", credits=3)
        course_b = Course(department_id=department.id, code="CB101", title="Course B", credits=3)
        db.add_all([course_a, course_b])
        db.flush()
        cv_a = CourseVersion(course_id=course_a.id, version_label="v1")
        cv_b = CourseVersion(course_id=course_b.id, version_label="v1")
        db.add_all([cv_a, cv_b])
        db.flush()
        course_a_id, course_b_id, cv_a_id, cv_b_id = course_a.id, course_b.id, cv_a.id, cv_b.id

        year = AcademicYear(
            label="2026-pr", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
        )
        db.add(year)
        db.flush()
        term = AcademicTerm(
            academic_year_id=year.id, name="Term", term_type="semester",
            start_date=date(2026, 1, 1), end_date=date(2026, 5, 1),
        )
        db.add(term)
        db.flush()
        term_id = term.id

    program_a_schema = provision_program_schema(institution.schema_name, "pra")
    program_b_schema = provision_program_schema(institution.schema_name, "prb")

    with session_scope(
        schema_translate_map={None: institution.schema_name, "program": program_a_schema}
    ) as pdb:
        pdb.add(CourseOffering(course_version_id=cv_a_id, academic_term_id=term_id))

    with session_scope(
        schema_translate_map={None: institution.schema_name, "program": program_b_schema}
    ) as pdb:
        pdb.add(CourseOffering(course_version_id=cv_b_id, academic_term_id=term_id))

    return {
        "program_a_id": program_a_id, "program_b_id": program_b_id,
        "course_a_id": course_a_id, "course_b_id": course_b_id,
    }


def _make_program_a_coordinator(schema_name: str, email: str, program_a_id: uuid.UUID) -> None:
    with session_scope(schema_translate_map={None: schema_name}) as db:
        user = User(email=email, password_hash=hash_password(_PASSWORD), full_name="Coordinator A")
        db.add(user)
        db.flush()
        role = db.query(Role).filter(Role.name == "Program Coordinator").one()
        db.add(
            UserRole(user_id=user.id, role_id=role.id, scope_type="program", scope_id=program_a_id)
        )


def _login(client: TestClient, slug: str, email: str) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": _PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert resp.status_code == 200, resp.text
    return {**_tenant_headers(slug), "Authorization": f"Bearer {resp.json()['access_token']}"}


def test_program_coordinator_can_grant_course_coordinator_within_own_program(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    ctx = _setup_two_programs(provisioned_tenant)
    _make_program_a_coordinator(
        provisioned_tenant.schema_name, "coord-a@example.org", ctx["program_a_id"]
    )
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        faculty = User(email="faculty1@example.org", password_hash="x", full_name="Faculty One")
        db.add(faculty)
        db.flush()
        faculty_id = faculty.id
        course_coordinator_role_id = (
            db.query(Role).filter(Role.name == "Course Coordinator").one().id
        )

    headers = _login(client, provisioned_tenant.slug, "coord-a@example.org")
    headers["X-Program-Code"] = "pra"

    resp = client.post(
        "/api/v1/program-roles/user-roles",
        json={
            "user_id": str(faculty_id), "role_id": str(course_coordinator_role_id),
            "scope_type": "course", "course_id": str(ctx["course_a_id"]),
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["scope_type"] == "course"
    assert resp.json()["scope_id"] == str(ctx["course_a_id"])


def test_program_coordinator_cannot_grant_course_from_another_program(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    ctx = _setup_two_programs(provisioned_tenant)
    _make_program_a_coordinator(
        provisioned_tenant.schema_name, "coord-a2@example.org", ctx["program_a_id"]
    )
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        faculty = User(email="faculty2@example.org", password_hash="x", full_name="Faculty Two")
        db.add(faculty)
        db.flush()
        faculty_id = faculty.id
        course_coordinator_role_id = (
            db.query(Role).filter(Role.name == "Course Coordinator").one().id
        )

    headers = _login(client, provisioned_tenant.slug, "coord-a2@example.org")
    headers["X-Program-Code"] = "pra"

    # course_b belongs to Program B, not Program A.
    resp = client.post(
        "/api/v1/program-roles/user-roles",
        json={
            "user_id": str(faculty_id), "role_id": str(course_coordinator_role_id),
            "scope_type": "course", "course_id": str(ctx["course_b_id"]),
        },
        headers=headers,
    )
    assert resp.status_code == 403, resp.text


def test_program_coordinator_cannot_grant_institution_administrator(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    ctx = _setup_two_programs(provisioned_tenant)
    _make_program_a_coordinator(
        provisioned_tenant.schema_name, "coord-a3@example.org", ctx["program_a_id"]
    )
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        target = User(email="target@example.org", password_hash="x", full_name="Target")
        db.add(target)
        db.flush()
        target_id = target.id
        admin_role_id = db.query(Role).filter(Role.name == "Institution Administrator").one().id

    headers = _login(client, provisioned_tenant.slug, "coord-a3@example.org")
    headers["X-Program-Code"] = "pra"

    resp = client.post(
        "/api/v1/program-roles/user-roles",
        json={
            "user_id": str(target_id), "role_id": str(admin_role_id),
            "scope_type": "program",
        },
        headers=headers,
    )
    assert resp.status_code == 403, resp.text


def test_program_coordinator_cannot_revoke_grant_from_another_program(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    ctx = _setup_two_programs(provisioned_tenant)
    _make_program_a_coordinator(
        provisioned_tenant.schema_name, "coord-a4@example.org", ctx["program_a_id"]
    )
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        faculty = User(email="faculty4@example.org", password_hash="x", full_name="Faculty Four")
        db.add(faculty)
        db.flush()
        cc_role = db.query(Role).filter(Role.name == "Course Coordinator").one()
        grant = UserRole(
            user_id=faculty.id, role_id=cc_role.id, scope_type="course",
            scope_id=ctx["course_b_id"],
        )
        db.add(grant)
        db.flush()
        grant_id = grant.id

    headers = _login(client, provisioned_tenant.slug, "coord-a4@example.org")
    headers["X-Program-Code"] = "pra"

    resp = client.delete(f"/api/v1/program-roles/user-roles/{grant_id}", headers=headers)
    assert resp.status_code == 403, resp.text


def test_program_coordinator_cannot_revoke_institution_wide_grant(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    ctx = _setup_two_programs(provisioned_tenant)
    _make_program_a_coordinator(
        provisioned_tenant.schema_name, "coord-a5@example.org", ctx["program_a_id"]
    )
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        faculty = User(email="faculty5@example.org", password_hash="x", full_name="Faculty Five")
        db.add(faculty)
        db.flush()
        faculty_role = db.query(Role).filter(Role.name == "Faculty").one()
        grant = UserRole(
            user_id=faculty.id, role_id=faculty_role.id, scope_type=None, scope_id=None
        )
        db.add(grant)
        db.flush()
        grant_id = grant.id

    headers = _login(client, provisioned_tenant.slug, "coord-a5@example.org")
    headers["X-Program-Code"] = "pra"

    resp = client.delete(f"/api/v1/program-roles/user-roles/{grant_id}", headers=headers)
    assert resp.status_code == 403, resp.text


def test_faculty_without_program_role_manage_is_denied(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    ctx = _setup_two_programs(provisioned_tenant)
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        user = User(
            email="plain-faculty@example.org", password_hash=hash_password(_PASSWORD),
            full_name="Plain",
        )
        db.add(user)
        db.flush()
        role = db.query(Role).filter(Role.name == "Faculty").one()
        db.add(
            UserRole(
                user_id=user.id, role_id=role.id, scope_type="program",
                scope_id=ctx["program_a_id"],
            )
        )

    headers = _login(client, provisioned_tenant.slug, "plain-faculty@example.org")
    headers["X-Program-Code"] = "pra"

    resp = client.get("/api/v1/program-roles/roster", headers=headers)
    assert resp.status_code == 403, resp.text


def test_default_role_grants_include_program_role_manage(provisioned_tenant: Institution) -> None:
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        permission = db.query(Permission).filter(Permission.code == "program_role.manage").one()
        for role_name in ("Program Administrator", "Program Coordinator"):
            role = db.query(Role).filter(Role.name == role_name).one()
            has_it = (
                db.query(RolePermission)
                .filter(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
                .one_or_none()
            )
            assert has_it is not None, f"{role_name} should hold program_role.manage"
