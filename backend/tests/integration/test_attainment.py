"""`app.services.attainment` — the core CO/PO attainment calculation engine
(ARCHITECTURE.md §6). This is the platform's actual intellectual product: a
silent regression here corrupts every accreditation number downstream, so it
gets real Postgres-backed integration tests rather than trusting the endpoint
layer's own (nonexistent) coverage.

Exercised against real Postgres schemas — the whole calculation depends on
cross-schema queries (institution-shared course_outcomes/questions joined
against program-scoped assessments/enrollments/marks), not something a pure
unit test with mocks could catch a wiring mistake in.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.db.session import session_scope
from app.models.public.institution import Institution
from app.models.tenant.assessments import (
    Assessment,
    AssessmentQuestion,
    AssessmentType,
    CourseAttainmentConfig,
    Question,
    QuestionCourseOutcomeMapping,
    StudentMark,
)
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering, CourseSection, StudentEnrollment
from app.models.tenant.identity import StudentProfile, User
from app.models.tenant.mappings import CourseOutcomePOMapping, MappingScale, MappingScaleLevel
from app.models.tenant.obe import CourseOutcome, ProgramOutcome
from app.models.tenant.org import (
    AcademicTerm,
    AcademicYear,
    Campus,
    Department,
    Program,
    ProgramVersion,
    School,
)
from app.services.attainment import (
    calculate_course_attainment,
    calculate_program_attainment,
    get_student_attainment_summary,
)
from app.services.tenancy import provision_program_schema

pytestmark = pytest.mark.usefixtures("require_database")


def _setup_course(
    institution: Institution, db_engine, *, course_code: str
) -> dict[str, uuid.UUID | str]:
    """One program, one course/course-version, one term, one section — the
    shared scaffolding every test below builds a CO/assessment/marks story
    on top of. Mirrors tests/integration/test_faculty_scope.py's pattern."""
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
        course_version = CourseVersion(course_id=course.id, version_label="v1")
        db.add(course_version)
        db.flush()
        course_version_id = course_version.id

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
        program_version_id = program_version.id

        offering = CourseOffering(
            course_version_id=course_version_id,
            academic_term_id=term_id,
            program_version_id=program_version_id,
        )
        pdb.add(offering)
        pdb.flush()
        section = CourseSection(course_offering_id=offering.id, section_code="1")
        pdb.add(section)
        pdb.flush()
        section_id = section.id

    return {
        "program_schema": program_schema,
        "program_id": program_id,
        "department_id": department.id,
        "program_version_id": program_version_id,
        "course_version_id": course_version_id,
        "term_id": term_id,
        "section_id": section_id,
    }


def _add_section(
    pdb: Session, *, department_id: uuid.UUID, program_version_id: uuid.UUID,
    term_id: uuid.UUID, course_code: str,
) -> tuple[uuid.UUID, uuid.UUID]:
    """A second Course/CourseVersion/CourseOffering/CourseSection under the
    same program version and term as `_setup_course`'s section -- lets a test
    put two COs (each with their own, differently-sized student roster) into
    the same program's attainment roll-up. Returns (course_version_id, section_id)."""
    course = Course(department_id=department_id, code=course_code, title="Course", credits=3)
    pdb.add(course)
    pdb.flush()
    course_version = CourseVersion(course_id=course.id, version_label="v1")
    pdb.add(course_version)
    pdb.flush()

    offering = CourseOffering(
        course_version_id=course_version.id, academic_term_id=term_id,
        program_version_id=program_version_id,
    )
    pdb.add(offering)
    pdb.flush()
    section = CourseSection(course_offering_id=offering.id, section_code="1")
    pdb.add(section)
    pdb.flush()

    return course_version.id, section.id


def _add_co_with_assessment(
    pdb: Session, *, course_version_id: uuid.UUID, section_id: uuid.UUID, term_id: uuid.UUID,
    co_code: str = "CO1", marks_allocated: Decimal = Decimal("10"),
) -> tuple[uuid.UUID, uuid.UUID]:
    """One CourseOutcome, assessed by one question worth `marks_allocated`
    marks in a single Assessment. Returns (course_outcome_id, assessment_question_id)."""
    co = CourseOutcome(
        course_version_id=course_version_id, code=co_code, statement=f"{co_code} statement",
        sequence=1,
    )
    pdb.add(co)
    pdb.flush()

    assessment_type = pdb.query(AssessmentType).filter(AssessmentType.name == "Quiz").one()
    assessment = Assessment(
        course_section_id=section_id, academic_term_id=term_id,
        assessment_type_id=assessment_type.id, title=f"Quiz for {co_code}",
        max_marks=marks_allocated,
    )
    pdb.add(assessment)
    pdb.flush()

    question = Question(
        course_version_id=course_version_id, text=f"Question for {co_code}",
        question_type="short_answer", marks=marks_allocated,
    )
    pdb.add(question)
    pdb.flush()

    aq = AssessmentQuestion(
        assessment_id=assessment.id, question_id=question.id,
        marks_allocated=marks_allocated, sequence=1,
    )
    pdb.add(aq)
    pdb.flush()

    pdb.add(QuestionCourseOutcomeMapping(question_id=question.id, course_outcome_id=co.id))
    pdb.flush()

    return co.id, aq.id


def _enroll_and_mark(
    pdb: Session, *, section_id: uuid.UUID, student_user_id: uuid.UUID,
    assessment_question_id: uuid.UUID | None, marks_obtained: Decimal | None,
    enrollment_status: str = "enrolled",
) -> uuid.UUID:
    """Enrolls a student into the section and (if a mark is given) records
    their score on one assessment question. `marks_obtained=None` leaves the
    student with no StudentMark row at all (never assessed that question)."""
    enrollment = StudentEnrollment(
        student_user_id=student_user_id, course_section_id=section_id,
        enrollment_status=enrollment_status,
    )
    pdb.add(enrollment)
    pdb.flush()
    if assessment_question_id is not None and marks_obtained is not None:
        pdb.add(
            StudentMark(
                assessment_question_id=assessment_question_id,
                student_enrollment_id=enrollment.id, marks_obtained=marks_obtained,
            )
        )
        pdb.flush()
    return enrollment.id


def _make_student(db: Session, email: str, *, batch_year: int | None = None) -> uuid.UUID:
    user = User(email=email, password_hash="x", full_name=email, is_active=True)
    db.add(user)
    db.flush()
    db.add(StudentProfile(user_id=user.id, student_code=email.split("@")[0], batch_year=batch_year))
    db.flush()
    return user.id


def test_student_attains_co_when_score_meets_threshold(
    provisioned_tenant: Institution, db_engine
) -> None:
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT101")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        s1 = _make_student(db, "s1-attains@example.org")
        s2 = _make_student(db, "s2-attains@example.org")
        s3 = _make_student(db, "s3-attains@example.org")

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        co_id, aq_id = _add_co_with_assessment(
            pdb, course_version_id=ctx["course_version_id"], section_id=ctx["section_id"],
            term_id=ctx["term_id"], marks_allocated=Decimal("10"),
        )
        # Default threshold is 60% of 10 marks = 6.
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s1,
            assessment_question_id=aq_id, marks_obtained=Decimal("8"),  # 80% -> attains
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s2,
            assessment_question_id=aq_id, marks_obtained=Decimal("7"),  # 70% -> attains
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s3,
            assessment_question_id=aq_id, marks_obtained=Decimal("4"),  # 40% -> does not attain
        )

        report = calculate_course_attainment(pdb, ctx["section_id"])

    assert report.total_enrolled == 3
    assert report.eligible_students == 3
    [co] = [o for o in report.outcomes if o.course_outcome_id == co_id]
    assert co.assessed is True
    assert co.students_attained == 2
    # 2/3 eligible students attained -> 66.67%, at/above the default 60% course-level threshold.
    assert co.attainment_percent == Decimal("66.67")
    assert co.is_attained is True


def test_course_level_threshold_not_met_marks_co_as_not_attained(
    provisioned_tenant: Institution, db_engine
) -> None:
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT102")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        s1 = _make_student(db, "below-1@example.org")
        s2 = _make_student(db, "below-2@example.org")
        s3 = _make_student(db, "below-3@example.org")

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        co_id, aq_id = _add_co_with_assessment(
            pdb, course_version_id=ctx["course_version_id"], section_id=ctx["section_id"],
            term_id=ctx["term_id"], marks_allocated=Decimal("10"),
        )
        # Only 1/3 students meets the individual 60% mark threshold.
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s1,
            assessment_question_id=aq_id, marks_obtained=Decimal("9"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s2,
            assessment_question_id=aq_id, marks_obtained=Decimal("2"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s3,
            assessment_question_id=aq_id, marks_obtained=Decimal("1"),
        )

        report = calculate_course_attainment(pdb, ctx["section_id"])

    [co] = [o for o in report.outcomes if o.course_outcome_id == co_id]
    assert co.students_attained == 1
    assert co.attainment_percent == Decimal("33.33")
    assert co.is_attained is False


def test_wi_treatment_exclude_drops_withdrawn_student_from_denominator(
    provisioned_tenant: Institution, db_engine
) -> None:
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT103")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        s1 = _make_student(db, "excl-1@example.org")
        s2 = _make_student(db, "excl-2@example.org")
        s3 = _make_student(db, "excl-withdrawn@example.org")

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        # min_students_percent=70 so the withdrawn student's absence/presence
        # actually flips is_attained between the two tests below.
        pdb.add(
            CourseAttainmentConfig(
                course_version_id=ctx["course_version_id"],
                min_marks_percent=Decimal("60"), min_students_percent=Decimal("70"),
                wi_treatment="exclude",
            )
        )
        co_id, aq_id = _add_co_with_assessment(
            pdb, course_version_id=ctx["course_version_id"], section_id=ctx["section_id"],
            term_id=ctx["term_id"], marks_allocated=Decimal("10"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s1,
            assessment_question_id=aq_id, marks_obtained=Decimal("10"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s2,
            assessment_question_id=aq_id, marks_obtained=Decimal("10"),
        )
        # Withdrawn, no marks entered at all.
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s3,
            assessment_question_id=None, marks_obtained=None, enrollment_status="withdrawn",
        )

        report = calculate_course_attainment(pdb, ctx["section_id"])

    assert report.total_enrolled == 3
    assert report.excluded_wi == 1
    assert report.eligible_students == 2
    [co] = [o for o in report.outcomes if o.course_outcome_id == co_id]
    assert co.eligible_students == 2
    assert co.attainment_percent == Decimal("100.00")
    assert co.is_attained is True


def test_wi_treatment_include_counts_withdrawn_student_as_not_attained(
    provisioned_tenant: Institution, db_engine
) -> None:
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT104")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        s1 = _make_student(db, "incl-1@example.org")
        s2 = _make_student(db, "incl-2@example.org")
        s3 = _make_student(db, "incl-withdrawn@example.org")

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        pdb.add(
            CourseAttainmentConfig(
                course_version_id=ctx["course_version_id"],
                min_marks_percent=Decimal("60"), min_students_percent=Decimal("70"),
                wi_treatment="include",
            )
        )
        co_id, aq_id = _add_co_with_assessment(
            pdb, course_version_id=ctx["course_version_id"], section_id=ctx["section_id"],
            term_id=ctx["term_id"], marks_allocated=Decimal("10"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s1,
            assessment_question_id=aq_id, marks_obtained=Decimal("10"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s2,
            assessment_question_id=aq_id, marks_obtained=Decimal("10"),
        )
        # Same withdrawn student, now included with no marks -> scores 0%.
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s3,
            assessment_question_id=None, marks_obtained=None, enrollment_status="withdrawn",
        )

        report = calculate_course_attainment(pdb, ctx["section_id"])

    assert report.eligible_students == 3
    [co] = [o for o in report.outcomes if o.course_outcome_id == co_id]
    assert co.eligible_students == 3
    assert co.students_attained == 2
    # 2/3 -> 66.67%, now BELOW the 70% threshold -- same data, opposite verdict from "exclude".
    assert co.attainment_percent == Decimal("66.67")
    assert co.is_attained is False


def test_co_without_mapped_questions_is_not_assessed(
    provisioned_tenant: Institution, db_engine
) -> None:
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT105")

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        # A CO with no assessment/question mapped to it at all.
        co = CourseOutcome(
            course_version_id=ctx["course_version_id"], code="CO-UNASSESSED",
            statement="Never assessed", sequence=1,
        )
        pdb.add(co)
        pdb.flush()

        report = calculate_course_attainment(pdb, ctx["section_id"])

    [co_report] = report.outcomes
    assert co_report.assessed is False
    assert co_report.attainment_percent is None
    assert co_report.is_attained is None


def test_batch_year_filter_narrows_course_attainment_to_cohort(
    provisioned_tenant: Institution, db_engine
) -> None:
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT106")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        s2025 = _make_student(db, "cohort-2025@example.org", batch_year=2025)
        s2026 = _make_student(db, "cohort-2026@example.org", batch_year=2026)

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        _co_id, aq_id = _add_co_with_assessment(
            pdb, course_version_id=ctx["course_version_id"], section_id=ctx["section_id"],
            term_id=ctx["term_id"], marks_allocated=Decimal("10"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s2025,
            assessment_question_id=aq_id, marks_obtained=Decimal("10"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=s2026,
            assessment_question_id=aq_id, marks_obtained=Decimal("0"),
        )

        unfiltered = calculate_course_attainment(pdb, ctx["section_id"])
        filtered_2025 = calculate_course_attainment(pdb, ctx["section_id"], batch_year=2025)

    assert unfiltered.eligible_students == 2
    assert filtered_2025.eligible_students == 1
    assert filtered_2025.outcomes[0].attainment_percent == Decimal("100.00")


def test_program_attainment_weights_co_by_mapping_strength_and_eligible_students(
    provisioned_tenant: Institution, db_engine
) -> None:
    """Two COs, each in its own section (own student roster), mapped to the
    same PO with different mapping-scale strengths (1 and 3) -- the PO's
    attainment percent must be the eligible-student-weighted CO percent,
    itself then weighted by mapping strength, not a plain average of the two
    CO percents (which would give a materially different, wrong number
    here)."""
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT107")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        strong_students = [
            _make_student(db, f"strong-{i}@example.org") for i in range(4)
        ]
        weak_students = [_make_student(db, f"weak-{i}@example.org") for i in range(2)]

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        scale = MappingScale(name="Strength Scale", is_default=False)
        pdb.add(scale)
        pdb.flush()
        level_weak = MappingScaleLevel(mapping_scale_id=scale.id, value=1, label="Low", sequence=1)
        level_strong = MappingScaleLevel(
            mapping_scale_id=scale.id, value=3, label="High", sequence=2
        )
        pdb.add_all([level_weak, level_strong])
        pdb.flush()

        # CO-A: its own section, 4 eligible students, all attain -> 100%. Mapped at strength 3.
        co_a_id, aq_a_id = _add_co_with_assessment(
            pdb, course_version_id=ctx["course_version_id"], section_id=ctx["section_id"],
            term_id=ctx["term_id"], co_code="CO-A", marks_allocated=Decimal("10"),
        )
        for student_id in strong_students:
            _enroll_and_mark(
                pdb, section_id=ctx["section_id"], student_user_id=student_id,
                assessment_question_id=aq_a_id, marks_obtained=Decimal("10"),
            )

        # CO-B: a second section under the same program, 2 eligible students,
        # none attain -> 0%. Mapped at strength 1.
        course_version_b_id, section_b_id = _add_section(
            pdb, department_id=ctx["department_id"], program_version_id=ctx["program_version_id"],
            term_id=ctx["term_id"], course_code="ATT107-B",
        )
        co_b_id, aq_b_id = _add_co_with_assessment(
            pdb, course_version_id=course_version_b_id, section_id=section_b_id,
            term_id=ctx["term_id"], co_code="CO-B", marks_allocated=Decimal("10"),
        )
        for student_id in weak_students:
            _enroll_and_mark(
                pdb, section_id=section_b_id, student_user_id=student_id,
                assessment_question_id=aq_b_id, marks_obtained=Decimal("0"),
            )

        program_outcome = ProgramOutcome(
            program_version_id=ctx["program_version_id"], code="PO1", statement="PO1 statement",
            sequence=1,
        )
        pdb.add(program_outcome)
        pdb.flush()

        pdb.add(
            CourseOutcomePOMapping(
                course_outcome_id=co_a_id, program_outcome_id=program_outcome.id,
                mapping_scale_level_id=level_strong.id,
            )
        )
        pdb.add(
            CourseOutcomePOMapping(
                course_outcome_id=co_b_id, program_outcome_id=program_outcome.id,
                mapping_scale_level_id=level_weak.id,
            )
        )
        pdb.flush()

        report = calculate_program_attainment(pdb, ctx["program_version_id"])

    [po] = report.outcomes
    assert po.assessed is True
    # CO-A=100% weight 3, CO-B=0% weight 1 -> (100*3 + 0*1) / (3+1) = 75.00
    assert po.attainment_percent == Decimal("75.00")
    assert po.is_attained is True
    assert {c.co_code for c in po.contributions} == {"CO-A", "CO-B"}


def test_program_attainment_excludes_zero_strength_mapping(
    provisioned_tenant: Institution, db_engine
) -> None:
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT108")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        student_id = _make_student(db, "zero-strength@example.org")

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        scale = MappingScale(name="No-mapping Scale", is_default=False)
        pdb.add(scale)
        pdb.flush()
        level_none = MappingScaleLevel(mapping_scale_id=scale.id, value=0, label="No", sequence=1)
        pdb.add(level_none)
        pdb.flush()

        co_id, aq_id = _add_co_with_assessment(
            pdb, course_version_id=ctx["course_version_id"], section_id=ctx["section_id"],
            term_id=ctx["term_id"], marks_allocated=Decimal("10"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=student_id,
            assessment_question_id=aq_id, marks_obtained=Decimal("10"),
        )

        program_outcome = ProgramOutcome(
            program_version_id=ctx["program_version_id"], code="PO-ZERO",
            statement="PO zero statement", sequence=1,
        )
        pdb.add(program_outcome)
        pdb.flush()
        pdb.add(
            CourseOutcomePOMapping(
                course_outcome_id=co_id, program_outcome_id=program_outcome.id,
                mapping_scale_level_id=level_none.id,
            )
        )
        pdb.flush()

        report = calculate_program_attainment(pdb, ctx["program_version_id"])

    [po] = report.outcomes
    assert po.assessed is False
    assert po.attainment_percent is None
    assert po.contributions == []


def test_student_attainment_summary_scopes_to_callers_own_enrollment(
    provisioned_tenant: Institution, db_engine
) -> None:
    """`/marks/my-attainment` never takes a student id from the client -- the
    calculation itself must not leak another student's marks/CO status into
    the report even when both students share the same section."""
    ctx = _setup_course(provisioned_tenant, db_engine, course_code="ATT109")

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        me = _make_student(db, "me@example.org")
        classmate = _make_student(db, "classmate@example.org")

    with session_scope(
        schema_translate_map={
            None: provisioned_tenant.schema_name, "program": ctx["program_schema"]
        }
    ) as pdb:
        _co_id, aq_id = _add_co_with_assessment(
            pdb, course_version_id=ctx["course_version_id"], section_id=ctx["section_id"],
            term_id=ctx["term_id"], marks_allocated=Decimal("10"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=me,
            assessment_question_id=aq_id, marks_obtained=Decimal("9"),
        )
        _enroll_and_mark(
            pdb, section_id=ctx["section_id"], student_user_id=classmate,
            assessment_question_id=aq_id, marks_obtained=Decimal("1"),
        )

        summary = get_student_attainment_summary(pdb, me, ctx["program_version_id"])

    [enrollment_report] = summary.enrollments
    assert enrollment_report.total_obtained == Decimal("9")
    [co_status] = enrollment_report.course_outcomes
    assert co_status.score_percent == Decimal("90.00")
    assert co_status.attained is True
