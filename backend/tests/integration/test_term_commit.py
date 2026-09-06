"""`app.services.term_commit` — Final Commit: the one permanent lock on
assessment/marks/attainment writes for a (program, term) pair, and the
"full access before commit" mechanics (implicit un-publish on edit,
implicit un-submit on mark edit) that make that lock meaningful rather than
redundant with the pre-existing WorkflowStatus/GradeSubmission locks.
Exercised against real Postgres schemas, mirroring
`tests/integration/test_attainment.py`'s scaffolding.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import WorkflowStatus
from app.db.session import session_scope
from app.main import app
from app.models.public.institution import Institution
from app.models.tenant.assessments import (
    Assessment,
    AssessmentQuestion,
    AssessmentType,
    AttainmentSnapshot,
    Question,
    QuestionCourseOutcomeMapping,
    StudentMark,
)
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering, CourseSection, StudentEnrollment
from app.models.tenant.identity import Role, StudentProfile, User, UserRole
from app.models.tenant.obe import CourseOutcome
from app.models.tenant.org import AcademicTerm, AcademicYear, Campus, Department, Program, School
from app.services.grades import submit_final_grades
from app.services.tenancy import provision_program_schema
from app.services.term_commit import (
    commit_term,
    ensure_term_not_committed,
    is_committable,
    reopen_grade_submission_if_submitted,
    revert_if_published,
    set_early_enable,
)

pytestmark = pytest.mark.usefixtures("require_database")

_PASSWORD = "SuperSecret123!"  # noqa: S105 - test-only credential


def _setup_course(
    institution: Institution, *, course_code: str, term_end_date: date
) -> dict[str, uuid.UUID | str]:
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
        program_code = program.code

        course = Course(department_id=department.id, code=course_code, title="Course", credits=3)
        db.add(course)
        db.flush()
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
            academic_year_id=academic_year.id, name=f"Term-{course_code}", term_type="semester",
            start_date=date(2026, 1, 1), end_date=term_end_date,
        )
        db.add(term)
        db.flush()
        term_id = term.id

        assessment_type = AssessmentType(name=f"Quiz-{course_code}", requires_documents=False)
        db.add(assessment_type)
        db.flush()
        assessment_type_id = assessment_type.id

        student = User(email=f"student-{course_code}@example.org", password_hash="x", full_name="S")
        db.add(student)
        db.flush()
        db.add(StudentProfile(user_id=student.id, student_code=f"S-{course_code}"))
        db.flush()
        student_id = student.id

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

        assessment = Assessment(
            course_section_id=section_id, academic_term_id=term_id,
            assessment_type_id=assessment_type_id, title="Quiz 1", max_marks=10,
            weight=100, status=WorkflowStatus.PUBLISHED,
        )
        pdb.add(assessment)
        pdb.flush()

        course_outcome = CourseOutcome(
            course_version_id=course_version_id, code="CO1", statement="CO1 statement", sequence=1,
        )
        pdb.add(course_outcome)
        pdb.flush()

        question = Question(
            course_version_id=course_version_id, text="Q1", question_type="short_answer", marks=10,
        )
        pdb.add(question)
        pdb.flush()
        aq = AssessmentQuestion(
            assessment_id=assessment.id, question_id=question.id, marks_allocated=10, sequence=1,
        )
        pdb.add(aq)
        pdb.flush()
        pdb.add(
            QuestionCourseOutcomeMapping(
                question_id=question.id, course_outcome_id=course_outcome.id
            )
        )
        pdb.flush()

        enrollment = StudentEnrollment(student_user_id=student_id, course_section_id=section_id)
        pdb.add(enrollment)
        pdb.flush()
        mark = StudentMark(
            assessment_question_id=aq.id, student_enrollment_id=enrollment.id, marks_obtained=8,
        )
        pdb.add(mark)
        pdb.flush()

    return {
        "program_schema": program_schema, "term_id": term_id, "section_id": section_id,
        "assessment_id": assessment.id, "mark_id": mark.id,
    }


def test_uncommitted_term_allows_editing_a_published_assessment_by_reverting_it(
    provisioned_tenant: Institution,
) -> None:
    ctx = _setup_course(
        provisioned_tenant, course_code="TC101", term_end_date=date(2026, 12, 31)
    )
    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        ensure_term_not_committed(pdb, ctx["section_id"])  # does not raise
        assessment = pdb.get(Assessment, ctx["assessment_id"])
        assert assessment.status == WorkflowStatus.PUBLISHED
        reverted = revert_if_published(assessment)
        assert reverted is True
        assert assessment.status == WorkflowStatus.APPROVED

        # A non-published assessment isn't touched.
        assessment.status = WorkflowStatus.DRAFT
        assert revert_if_published(assessment) is False
        assert assessment.status == WorkflowStatus.DRAFT


def test_uncommitted_term_allows_reopening_submitted_grades(
    provisioned_tenant: Institution,
) -> None:
    ctx = _setup_course(
        provisioned_tenant, course_code="TC102", term_end_date=date(2026, 12, 31)
    )
    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        submitter_id = uuid.uuid4()
        with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
            u = User(email="submitter-tc102@example.org", password_hash="x", full_name="U")
            db.add(u)
            db.flush()
            submitter_id = u.id

        submission = submit_final_grades(pdb, ctx["section_id"], submitter_id)
        assert submission.status == "submitted"
        [snapshot] = pdb.query(AttainmentSnapshot).filter(
            AttainmentSnapshot.grade_submission_id == submission.id
        ).all()
        first_snapshot_id = snapshot.id

        reopened = reopen_grade_submission_if_submitted(pdb, ctx["section_id"])
        assert reopened is not None
        assert reopened.status == "draft"
        assert reopened.submitted_by is None

        # Editing again with a fresh mark and resubmitting must not leave
        # the first submission's snapshot rows lying around alongside new
        # ones.
        mark = pdb.get(StudentMark, ctx["mark_id"])
        mark.marks_obtained = 10
        pdb.add(mark)
        pdb.flush()
        resubmission = submit_final_grades(pdb, ctx["section_id"], submitter_id)
        assert resubmission.id == submission.id  # same GradeSubmission row, reused
        snapshots_after = pdb.query(AttainmentSnapshot).filter(
            AttainmentSnapshot.grade_submission_id == submission.id
        ).all()
        assert len(snapshots_after) == 1
        assert snapshots_after[0].id != first_snapshot_id
        # 10/10 now (was 8/10 pre-edit) -> 100% attainment in the fresh snapshot.
        assert snapshots_after[0].attainment_percent == pytest.approx(100.0)


def test_commit_requires_term_ended_or_manually_enabled(provisioned_tenant: Institution) -> None:
    ctx = _setup_course(
        provisioned_tenant, course_code="TC103", term_end_date=date.today() + timedelta(days=30)
    )
    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        term = pdb.get(AcademicTerm, ctx["term_id"])
        assert is_committable(term, None) is False
        with pytest.raises(HTTPException) as exc_info:
            commit_term(pdb, term, uuid.uuid4())
        assert exc_info.value.status_code == 403

        commit = set_early_enable(pdb, ctx["term_id"], True)
        assert commit.manually_enabled is True
        assert is_committable(term, commit) is True


def test_committing_a_term_permanently_locks_writes_and_cannot_be_recommitted(
    provisioned_tenant: Institution,
) -> None:
    ctx = _setup_course(
        provisioned_tenant, course_code="TC104", term_end_date=date(2020, 1, 1)  # already ended
    )
    committer_id = uuid.uuid4()
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        u = User(email="committer-tc104@example.org", password_hash="x", full_name="C")
        db.add(u)
        db.flush()
        committer_id = u.id

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        ensure_term_not_committed(pdb, ctx["section_id"])  # does not raise, not committed yet
        term = pdb.get(AcademicTerm, ctx["term_id"])
        commit = commit_term(pdb, term, committer_id)
        assert commit.is_committed is True
        assert commit.committed_by == committer_id
        assert commit.committed_at is not None

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        with pytest.raises(HTTPException) as exc_info:
            ensure_term_not_committed(pdb, ctx["section_id"])
        assert exc_info.value.status_code == 403

        # Permanent: re-committing is rejected, not a silent no-op.
        term = pdb.get(AcademicTerm, ctx["term_id"])
        with pytest.raises(HTTPException) as exc_info2:
            commit_term(pdb, term, committer_id)
        assert exc_info2.value.status_code == 409


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _tenant_headers(slug: str) -> dict[str, str]:
    return {settings.dev_tenant_header: slug}


def test_only_term_commit_manage_holder_can_commit(
    client: TestClient, provisioned_tenant: Institution
) -> None:
    ctx = _setup_course(
        provisioned_tenant, course_code="TC105", term_end_date=date(2020, 1, 1)
    )
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        program = db.query(Program).filter(Program.code == "p-TC105").one()
        program_id = program.id
        user = User(
            email="no-commit-perm@example.org", password_hash=hash_password(_PASSWORD),
            full_name="No Perm",
        )
        db.add(user)
        db.flush()
        role = db.query(Role).filter(Role.name == "Program Coordinator").one()
        db.add(
            UserRole(
                user_id=user.id, role_id=role.id, scope_type="program", scope_id=program_id
            )
        )

    login_resp = client.post(
        "/api/v1/auth/login", json={"email": "no-commit-perm@example.org", "password": _PASSWORD},
        headers=_tenant_headers(provisioned_tenant.slug),
    )
    assert login_resp.status_code == 200, login_resp.text
    headers = {
        **_tenant_headers(provisioned_tenant.slug),
        "Authorization": f"Bearer {login_resp.json()['access_token']}",
        "X-Program-Code": "p-TC105",
    }
    resp = client.post(f"/api/v1/term-commit/{ctx['term_id']}/commit", headers=headers)
    assert resp.status_code == 403, resp.text
