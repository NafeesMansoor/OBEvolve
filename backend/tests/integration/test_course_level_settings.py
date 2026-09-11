"""Course-Level Settings and Approval Workflow
(docs/course_level_settings_and_approval_workflow.md).

Exercised against real Postgres schemas — `app.services.course_type_config`
resolves a section's course type across the tenant/program schema boundary
(`CourseSection` -> `CourseOffering` -> `CourseVersion` -> `Course` ->
`CourseType`, program-scoped `CourseTypeSectionConfig`), and the migration
backfill behavior (0019_course_types / 0012_course_type_section_configs)
that keeps every pre-existing course fully unlocked is exactly the kind of
cross-schema wiring a pure unit test with mocks would not catch a mistake
in — mirrors `tests/integration/test_attainment.py`'s and
`test_faculty_scope.py`'s approach.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import HTTPException

from app.db.session import session_scope
from app.models.public.institution import Institution
from app.models.tenant.change_requests import CourseChangeRequest
from app.models.tenant.course_type_config import CourseTypeSectionConfig
from app.models.tenant.courses.catalog import Course, CourseType, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering, CourseSection
from app.models.tenant.identity import Role, User, UserRole
from app.models.tenant.obe.outcomes import CourseOutcome
from app.models.tenant.org import AcademicTerm, AcademicYear, Campus, Department, Program, School
from app.services.course_type_config import (
    SECTION_APPROVAL_TIERS,
    apply_change_request,
    compute_import_preview,
    ensure_direct_enrollment_write_allowed,
    ensure_section_enabled,
    resolve_section_config,
)
from app.services.rbac import user_has_permission
from app.services.tenancy import provision_program_schema

pytestmark = pytest.mark.usefixtures("require_database")


def _setup_course(institution: Institution, *, course_code: str) -> dict[str, uuid.UUID | str]:
    with session_scope(schema_translate_map={None: institution.schema_name}) as db:
        campus = Campus(institution_id=institution.id, name="Main Campus", code=f"C{course_code}")
        db.add(campus)
        db.flush()
        school = School(campus_id=campus.id, name="School of Eng", code=f"S{course_code}")
        db.add(school)
        db.flush()
        department = Department(school_id=school.id, name="CSE", code=f"D{course_code}")
        db.add(department)
        db.flush()
        program = Program(department_id=department.id, name="BSc CSE", code=f"p-{course_code}")
        db.add(program)
        db.flush()
        program_id = program.id
        program_code = program.code

        course = Course(department_id=department.id, code=course_code, title="Course", credits=3)
        db.add(course)
        db.flush()
        course_id = course.id
        course_version = CourseVersion(course_id=course.id, version_label="v1")
        db.add(course_version)
        db.flush()
        course_version_id = course_version.id

        academic_year = AcademicYear(
            label=f"2026-{course_code}", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
        )
        db.add(academic_year)
        db.flush()
        term = AcademicTerm(
            academic_year_id=academic_year.id,
            name="Spring 2026",
            term_type="spring",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 5, 1),
        )
        db.add(term)
        db.flush()
        term_id = term.id

    program_schema = provision_program_schema(institution.schema_name, program_code)

    with session_scope(
        schema_translate_map={None: institution.schema_name, "program": program_schema}
    ) as pdb:
        offering = CourseOffering(course_version_id=course_version_id, academic_term_id=term_id)
        pdb.add(offering)
        pdb.flush()
        section = CourseSection(course_offering_id=offering.id, section_code="1")
        pdb.add(section)
        pdb.flush()
        section_id = section.id

    return {
        "program_schema": program_schema,
        "program_id": program_id,
        "course_id": course_id,
        "course_version_id": course_version_id,
        "section_id": section_id,
    }


def _make_user(institution: Institution, email: str) -> uuid.UUID:
    with session_scope(schema_translate_map={None: institution.schema_name}) as db:
        user = User(email=email, password_hash="x", full_name=email, is_active=True)
        db.add(user)
        db.flush()
        return user.id


def _make_course_type(institution: Institution, *, name: str) -> uuid.UUID:
    with session_scope(schema_translate_map={None: institution.schema_name}) as db:
        course_type = CourseType(name=name)
        db.add(course_type)
        db.flush()
        return course_type.id


def _set_section_config(
    institution: Institution, program_schema: str, *, course_type_id: uuid.UUID, section_key: str,
    is_enabled: bool,
) -> None:
    with session_scope(
        schema_translate_map={None: institution.schema_name, "program": program_schema}
    ) as pdb:
        pdb.add(
            CourseTypeSectionConfig(
                course_type_id=course_type_id, section_key=section_key, is_enabled=is_enabled
            )
        )
        pdb.flush()


def test_unclassified_course_is_fully_locked(provisioned_tenant: Institution) -> None:
    ctx = _setup_course(provisioned_tenant, course_code="CLS101")
    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        assert resolve_section_config(pdb, ctx["section_id"]) == {
            "overview": False, "settings": False, "students": False, "assessments": False,
        }
        with pytest.raises(HTTPException) as exc_info:
            ensure_section_enabled(pdb, ctx["section_id"], "overview")
        assert exc_info.value.status_code == 403


def test_disabled_section_is_locked_even_when_classified(provisioned_tenant: Institution) -> None:
    ctx = _setup_course(provisioned_tenant, course_code="CLS102")
    course_type_id = _make_course_type(provisioned_tenant, name="Theory-CLS102")
    _set_section_config(
        provisioned_tenant, ctx["program_schema"], course_type_id=course_type_id,
        section_key="settings", is_enabled=False,
    )
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        course = db.get(Course, ctx["course_id"])
        course.course_type_id = course_type_id
        db.add(course)
        db.flush()

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        with pytest.raises(HTTPException) as exc_info:
            ensure_section_enabled(pdb, ctx["section_id"], "settings")
        assert exc_info.value.status_code == 403


def test_enabled_section_passes_gate_and_resolves_correctly(
    provisioned_tenant: Institution,
) -> None:
    ctx = _setup_course(provisioned_tenant, course_code="CLS103")
    course_type_id = _make_course_type(provisioned_tenant, name="Theory-CLS103")
    _set_section_config(
        provisioned_tenant, ctx["program_schema"], course_type_id=course_type_id,
        section_key="overview", is_enabled=True,
    )
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        course = db.get(Course, ctx["course_id"])
        course.course_type_id = course_type_id
        db.add(course)
        db.flush()

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        ensure_section_enabled(pdb, ctx["section_id"], "overview")  # does not raise
        config = resolve_section_config(pdb, ctx["section_id"])
        assert config == {
            "overview": True, "settings": False, "students": False, "assessments": False,
        }
        with pytest.raises(HTTPException):
            ensure_section_enabled(pdb, ctx["section_id"], "settings")


def test_provisioning_creates_a_fully_enabled_general_course_type(
    provisioned_tenant: Institution,
) -> None:
    """Regression guard for the 0019/0012 migration backfill: any
    institution that already had courses before this feature shipped must
    NOT come out with them locked (see those migrations' comments) — the
    "General" type they get backfilled onto must itself have all four
    sections enabled, which this checks the migration actually seeded. (A
    freshly created course in a freshly provisioned test tenant has no
    pre-existing rows to backfill — this checks the seeded type + config
    directly rather than a backfill that has nothing to act on here.)"""
    ctx = _setup_course(provisioned_tenant, course_code="CLS104")
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        general = db.query(CourseType).filter(CourseType.name == "General").one()
        assert general.is_active is True
        general_id = general.id

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        rows = {
            row.section_key: row.is_enabled
            for row in pdb.query(CourseTypeSectionConfig)
            .filter(CourseTypeSectionConfig.course_type_id == general_id)
            .all()
        }
        assert rows == {
            "overview": True, "settings": True, "students": True, "assessments": True,
        }


def test_apply_scalar_target_writes_course_description(provisioned_tenant: Institution) -> None:
    ctx = _setup_course(provisioned_tenant, course_code="CLS105")
    requester_id = _make_user(provisioned_tenant, "teacher-cls105@example.org")
    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        change = CourseChangeRequest(
            course_section_id=ctx["section_id"], section_key="overview", target_field="description",
            proposed_value_json={"value": "New overview text"}, reason="typo fix",
            status="approved", requested_by=requester_id,
        )
        pdb.add(change)
        pdb.flush()
        apply_change_request(pdb, change)
        assert change.apply_status == "applied"
        assert change.apply_error is None

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        course = db.get(Course, ctx["course_id"])
        assert course.description == "New overview text"


def test_apply_outcomes_target_upserts_by_code(provisioned_tenant: Institution) -> None:
    ctx = _setup_course(provisioned_tenant, course_code="CLS106")
    requester_id = _make_user(provisioned_tenant, "teacher-cls106@example.org")
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        existing = CourseOutcome(
            course_version_id=ctx["course_version_id"], code="CO1", statement="Old statement",
            sequence=1,
        )
        db.add(existing)
        db.flush()

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        change = CourseChangeRequest(
            course_section_id=ctx["section_id"], section_key="settings", target_field="outcomes",
            proposed_value_json={
                "outcomes": [
                    {"code": "CO1", "statement": "Updated statement", "sequence": 1},
                    {"code": "CO2", "statement": "Brand new CO", "sequence": 2},
                ]
            },
            reason="curriculum refresh", status="approved", requested_by=requester_id,
        )
        pdb.add(change)
        pdb.flush()
        apply_change_request(pdb, change)
        assert change.apply_status == "applied"

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        outcomes = {
            co.code: co.statement
            for co in db.query(CourseOutcome)
            .filter(CourseOutcome.course_version_id == ctx["course_version_id"])
            .all()
        }
        assert outcomes == {"CO1": "Updated statement", "CO2": "Brand new CO"}


def test_apply_records_failure_without_raising_when_target_no_longer_exists(
    provisioned_tenant: Institution,
) -> None:
    ctx = _setup_course(provisioned_tenant, course_code="CLS107")
    requester_id = _make_user(provisioned_tenant, "teacher-cls107@example.org")
    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        change = CourseChangeRequest(
            course_section_id=ctx["section_id"], section_key="students",
            target_field="enrollment_status",
            proposed_value_json={"action": "update_status", "enrollment_id": str(uuid.uuid4())},
            reason="withdrawal", status="approved", requested_by=requester_id,
        )
        pdb.add(change)
        pdb.flush()
        apply_change_request(pdb, change)
        assert change.apply_status == "failed"
        assert change.apply_error is not None


def test_grading_policy_target_is_skipped_not_guessed(provisioned_tenant: Institution) -> None:
    """No safe automatic target exists for `grading_policy` (a course has no
    owning FK to rewrite — see `app.services.course_type_config`'s
    docstring) — it must record `apply_status="skipped"`, never silently
    invent new semantics."""
    ctx = _setup_course(provisioned_tenant, course_code="CLS108")
    requester_id = _make_user(provisioned_tenant, "teacher-cls108@example.org")
    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        change = CourseChangeRequest(
            course_section_id=ctx["section_id"], section_key="settings",
            target_field="grading_policy", proposed_value_json={"value": "some new policy"},
            reason="policy change", status="approved", requested_by=requester_id,
        )
        pdb.add(change)
        pdb.flush()
        apply_change_request(pdb, change)
        assert change.apply_status == "skipped"


def test_enrollment_write_gate_allows_authority_blocks_assigned_teacher() -> None:
    ensure_direct_enrollment_write_allowed(True)  # does not raise
    with pytest.raises(HTTPException) as exc_info:
        ensure_direct_enrollment_write_allowed(False)
    assert exc_info.value.status_code == 403


def test_section_approval_tiers_match_spec() -> None:
    assert SECTION_APPROVAL_TIERS == {
        "overview": 1, "students": 1, "settings": 2, "assessments": 2,
    }


def test_default_role_grants_for_staged_review_permissions(
    provisioned_tenant: Institution,
) -> None:
    """Section Coordinator gets stage-1 review;
    Program Coordinator gets stage-2 final review + course_type.manage —
    the RBAC split this whole workflow's authorization hinges on
    (app.core.permissions/app.seed.default_roles)."""
    ctx = _setup_course(provisioned_tenant, course_code="CLS109")
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        admin_user = User(email="admin-cls109@example.org", password_hash="x", full_name="A")
        coordinator_user = User(email="coord-cls109@example.org", password_hash="x", full_name="C")
        db.add_all([admin_user, coordinator_user])
        db.flush()
        admin_role = db.query(Role).filter(Role.name == "Section Coordinator").one()
        coordinator_role = db.query(Role).filter(Role.name == "Program Coordinator").one()
        db.add_all(
            [
                UserRole(
                    user_id=admin_user.id, role_id=admin_role.id, scope_type="program",
                    scope_id=ctx["program_id"],
                ),
                UserRole(
                    user_id=coordinator_user.id, role_id=coordinator_role.id, scope_type="program",
                    scope_id=ctx["program_id"],
                ),
            ]
        )
        db.flush()

        assert user_has_permission(
            db, admin_user.id, "course_change_request.review_admin",
            scope_type="program", scope_id=ctx["program_id"],
        )
        assert not user_has_permission(
            db, admin_user.id, "course_change_request.review_program",
            scope_type="program", scope_id=ctx["program_id"],
        )
        assert user_has_permission(
            db, coordinator_user.id, "course_change_request.review_program",
            scope_type="program", scope_id=ctx["program_id"],
        )
        assert user_has_permission(
            db, coordinator_user.id, "course_type.manage",
            scope_type="program", scope_id=ctx["program_id"],
        )


def test_import_preview_diffs_scalar_and_outcome_fields_without_writing(
    provisioned_tenant: Institution,
) -> None:
    target_ctx = _setup_course(provisioned_tenant, course_code="CLS110A")
    source_ctx = _setup_course(provisioned_tenant, course_code="CLS110B")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        target_course = db.get(Course, target_ctx["course_id"])
        target_course.description = "Old description"
        db.add(target_course)

        source_course = db.get(Course, source_ctx["course_id"])
        source_course.description = "Source description"
        db.add(source_course)
        db.add(
            CourseOutcome(
                course_version_id=source_ctx["course_version_id"], code="CO1",
                statement="Source CO1", sequence=1,
            )
        )
        db.flush()

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": target_ctx["program_schema"]
        }
    ) as pdb:
        preview = compute_import_preview(
            pdb, target_ctx["section_id"], source_ctx["course_version_id"]
        )

    assert preview["description"]["current_value"] == {"value": "Old description"}
    assert preview["description"]["proposed_value"] == {"value": "Source description"}
    assert preview["outcomes"]["current_value"] == {"outcomes": []}
    assert preview["outcomes"]["proposed_value"] == {
        "outcomes": [
            {
                "code": "CO1", "statement": "Source CO1", "sequence": 1,
                "delivery_methods": None, "assessment_tools": None,
            }
        ]
    }

    # Purely read-only: the target's real data must be untouched.
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        assert db.get(Course, target_ctx["course_id"]).description == "Old description"


def test_import_preview_404s_for_unknown_source_version(provisioned_tenant: Institution) -> None:
    ctx = _setup_course(provisioned_tenant, course_code="CLS111")
    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        with pytest.raises(HTTPException) as exc_info:
            compute_import_preview(pdb, ctx["section_id"], uuid.uuid4())
        assert exc_info.value.status_code == 404


def test_apply_outcomes_rejects_free_text_instead_of_silently_no_oping(
    provisioned_tenant: Institution,
) -> None:
    """Regression: a free-text "outcomes" proposal (no structured
    `outcomes` list — e.g. CourseSettingsTab's plain-textarea Edit button)
    used to silently apply an *empty* upsert list and report
    apply_status="applied", discarding the teacher's request without a
    trace. It must now be recorded as a failed apply instead."""
    ctx = _setup_course(provisioned_tenant, course_code="CLS112")
    requester_id = _make_user(provisioned_tenant, "teacher-cls112@example.org")
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        existing = CourseOutcome(
            course_version_id=ctx["course_version_id"], code="CO1", statement="Untouched",
            sequence=1,
        )
        db.add(existing)
        db.flush()

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        change = CourseChangeRequest(
            course_section_id=ctx["section_id"], section_key="settings", target_field="outcomes",
            proposed_value_json={"value": "Please add a CO about ethics"},
            reason="curriculum feedback", status="approved", requested_by=requester_id,
        )
        pdb.add(change)
        pdb.flush()
        apply_change_request(pdb, change)
        assert change.apply_status == "failed"
        assert change.apply_error is not None

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        [co] = db.query(CourseOutcome).filter(
            CourseOutcome.course_version_id == ctx["course_version_id"]
        ).all()
        assert co.statement == "Untouched"
