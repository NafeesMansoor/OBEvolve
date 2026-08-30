"""`app.services.faculty_scope` — Faculty Module BR-03 ("faculty can only
manage courses/sections they are assigned to"). Exercised against real
Postgres schemas (a plain instructor's `FacultyAssignment` row vs. a
Program Coordinator's program-wide `section.manage` grant) since the whole
point is a real query filter over real cross-schema data, not a pure
function — see `app.services.faculty_scope`'s module docstring for why this
isn't a new RBAC scope type.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.session import session_scope
from app.models.public.institution import Institution
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering, CourseSection, FacultyAssignment
from app.models.tenant.identity import Role, User, UserRole
from app.models.tenant.org import (
    AcademicTerm,
    AcademicYear,
    Campus,
    Department,
    Program,
    ProgramVersion,
    School,
)
from app.services.faculty_scope import (
    ensure_assigned_to_section,
    ensure_current_term,
    ensure_section_access,
    get_my_course_section_ids,
    is_section_authority,
)
from app.services.tenancy import provision_program_schema

pytestmark = pytest.mark.usefixtures("require_database")


def _make_user(db: Session, email: str) -> User:
    user = User(email=email, password_hash="x", full_name=email, is_active=True)
    db.add(user)
    db.flush()
    return user


def _setup_program_with_two_sections(
    institution: Institution, db_engine
) -> tuple[str, uuid.UUID, uuid.UUID, uuid.UUID]:
    """Returns (program_schema, program_id, section_1_id, section_2_id)."""
    with session_scope(schema_translate_map={None: institution.schema_name}) as db:
        campus = Campus(institution_id=institution.id, name="Main Campus", code="MAIN")
        db.add(campus)
        db.flush()
        school = School(campus_id=campus.id, name="School of Eng", code="ENG")
        db.add(school)
        db.flush()
        department = Department(school_id=school.id, name="CSE", code="CSE")
        db.add(department)
        db.flush()
        program = Program(department_id=department.id, name="BSc CSE", code="bscse-fac")
        db.add(program)
        db.flush()
        program_id = program.id
        program_code = program.code

        course = Course(department_id=department.id, code="CSE101", title="Intro", credits=3)
        db.add(course)
        db.flush()
        course_version = CourseVersion(course_id=course.id, version_label="v1")
        db.add(course_version)
        db.flush()

        academic_year = AcademicYear(
            label="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)
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
        course_version_id = course_version.id
        academic_year_id = academic_year.id

    program_schema = provision_program_schema(institution.schema_name, program_code)

    with session_scope(
        schema_translate_map={None: institution.schema_name, "program": program_schema}
    ) as pdb:
        program_version = ProgramVersion(
            program_id=program_id,
            version_label="v1",
            effective_academic_year_id=academic_year_id,
            status="draft",
        )
        pdb.add(program_version)
        pdb.flush()

        offering = CourseOffering(course_version_id=course_version_id, academic_term_id=term_id)
        pdb.add(offering)
        pdb.flush()

        section_1 = CourseSection(course_offering_id=offering.id, section_code="1")
        section_2 = CourseSection(course_offering_id=offering.id, section_code="2")
        pdb.add_all([section_1, section_2])
        pdb.flush()
        return program_schema, program_id, section_1.id, section_2.id


def test_instructor_sees_only_assigned_section(provisioned_tenant: Institution, db_engine) -> None:
    program_schema, _program_id, section_1_id, section_2_id = _setup_program_with_two_sections(
        provisioned_tenant, db_engine
    )

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        faculty = _make_user(db, "instructor@example.org")
        faculty_id = faculty.id

    with session_scope(
        schema_translate_map={None: provisioned_tenant.schema_name, "program": program_schema}
    ) as pdb:
        pdb.add(
            FacultyAssignment(
                course_section_id=section_1_id, faculty_user_id=faculty_id, role="instructor"
            )
        )
        pdb.flush()

        assert get_my_course_section_ids(pdb, faculty_id) == {section_1_id}
        assert is_section_authority(pdb, faculty_id) is False

        ensure_section_access(pdb, faculty_id, section_1_id)  # does not raise

        with pytest.raises(HTTPException) as exc_info:
            ensure_section_access(pdb, faculty_id, section_2_id)
        assert exc_info.value.status_code == 403


def test_program_coordinator_is_a_section_authority(
    provisioned_tenant: Institution, db_engine
) -> None:
    program_schema, program_id, _section_1_id, section_2_id = _setup_program_with_two_sections(
        provisioned_tenant, db_engine
    )

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        coordinator = _make_user(db, "coordinator@example.org")
        coordinator_id = coordinator.id
        role = db.query(Role).filter(Role.name == "Program Coordinator").one()
        db.add(
            UserRole(
                user_id=coordinator_id,
                role_id=role.id,
                scope_type="program",
                scope_id=program_id,
            )
        )
        db.flush()

    with session_scope(
        schema_translate_map={None: provisioned_tenant.schema_name, "program": program_schema}
    ) as pdb:
        assert is_section_authority(pdb, coordinator_id, program_id) is True
        # No FacultyAssignment row at all, but authority bypasses the filter.
        ensure_section_access(pdb, coordinator_id, section_2_id, program_id)  # does not raise

        # The grant is scoped to *this* program — it must not leak into a
        # check against some other program's id.
        other_program_id = uuid.uuid4()
        assert is_section_authority(pdb, coordinator_id, other_program_id) is False
        with pytest.raises(HTTPException):
            ensure_section_access(pdb, coordinator_id, section_2_id, other_program_id)


def test_program_coordinator_cannot_enter_marks_for_a_section_they_do_not_teach(
    provisioned_tenant: Institution, db_engine
) -> None:
    """Regression for a real finding: a Program Coordinator (program-wide
    `section.manage`, no personal `FacultyAssignment` on this section) could
    call `bulk_upsert_student_marks`/`create_assessment`/grade-submission
    because those endpoints used `ensure_section_access` (which
    `is_section_authority` bypasses for `section.manage` holders). Marks/
    grades/assessment-authoring/course-file-upload must use
    `ensure_assigned_to_section` instead, which has no such bypass — see
    `app.services.faculty_scope`'s module docstring."""
    program_schema, program_id, _section_1_id, section_2_id = _setup_program_with_two_sections(
        provisioned_tenant, db_engine
    )

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        coordinator = _make_user(db, "coordinator2@example.org")
        coordinator_id = coordinator.id
        role = db.query(Role).filter(Role.name == "Program Coordinator").one()
        db.add(
            UserRole(
                user_id=coordinator_id,
                role_id=role.id,
                scope_type="program",
                scope_id=program_id,
            )
        )
        db.flush()

    with session_scope(
        schema_translate_map={None: provisioned_tenant.schema_name, "program": program_schema}
    ) as pdb:
        # Broad authority still holds (section.manage-gated actions unaffected)...
        assert is_section_authority(pdb, coordinator_id, program_id) is True
        ensure_section_access(pdb, coordinator_id, section_2_id, program_id)  # does not raise

        # ...but the strict, no-bypass check correctly rejects them: no
        # FacultyAssignment row means no marks/grades/assessment authoring,
        # even for a program-wide administrator.
        with pytest.raises(HTTPException) as exc_info:
            ensure_assigned_to_section(pdb, coordinator_id, section_2_id)
        assert exc_info.value.status_code == 403


def test_faculty_cannot_write_to_a_previous_semester_section(
    provisioned_tenant: Institution, db_engine
) -> None:
    """BR-01: "Faculty editing capabilities apply only to courses in the
    current active semester." An assigned instructor still passes the
    ownership check (`get_my_course_section_ids`), but `ensure_current_term`
    — called from inside `ensure_assigned_to_section` — must independently
    reject the write once the section's `AcademicTerm.is_active` is False,
    even though nothing about the `FacultyAssignment` row itself changed."""
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        campus = Campus(institution_id=provisioned_tenant.id, name="Main Campus 2", code="MAIN2")
        db.add(campus)
        db.flush()
        school = School(campus_id=campus.id, name="School of Eng 2", code="ENG2")
        db.add(school)
        db.flush()
        department = Department(school_id=school.id, name="CSE2", code="CSE2")
        db.add(department)
        db.flush()
        program = Program(department_id=department.id, name="BSc CSE 2", code="bscse-fac2")
        db.add(program)
        db.flush()
        program_id = program.id
        program_code = program.code

        course = Course(department_id=department.id, code="CSE102", title="Intro 2", credits=3)
        db.add(course)
        db.flush()
        course_version = CourseVersion(course_id=course.id, version_label="v1")
        db.add(course_version)
        db.flush()
        course_version_id = course_version.id

        academic_year = AcademicYear(
            label="2025", start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        db.add(academic_year)
        db.flush()
        term = AcademicTerm(
            academic_year_id=academic_year.id,
            name="Spring 2025",
            term_type="spring",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 5, 1),
            is_active=False,
        )
        db.add(term)
        db.flush()
        term_id = term.id
        academic_year_id = academic_year.id

        faculty = _make_user(db, "instructor-old-term@example.org")
        faculty_id = faculty.id

    program_schema = provision_program_schema(provisioned_tenant.schema_name, program_code)

    with session_scope(
        schema_translate_map={None: provisioned_tenant.schema_name, "program": program_schema}
    ) as pdb:
        pdb.add(
            ProgramVersion(
                program_id=program_id,
                version_label="v1",
                effective_academic_year_id=academic_year_id,
                status="draft",
            )
        )
        pdb.flush()

        offering = CourseOffering(course_version_id=course_version_id, academic_term_id=term_id)
        pdb.add(offering)
        pdb.flush()
        section = CourseSection(course_offering_id=offering.id, section_code="1")
        pdb.add(section)
        pdb.flush()
        section_id = section.id

        pdb.add(
            FacultyAssignment(
                course_section_id=section_id, faculty_user_id=faculty_id, role="instructor"
            )
        )
        pdb.flush()

        # Still assigned...
        assert section_id in get_my_course_section_ids(pdb, faculty_id)
        # ...but the term is over, so no write is allowed.
        with pytest.raises(HTTPException) as exc_info:
            ensure_current_term(pdb, section_id)
        assert exc_info.value.status_code == 403

        with pytest.raises(HTTPException) as exc_info:
            ensure_assigned_to_section(pdb, faculty_id, section_id)
        assert exc_info.value.status_code == 403
