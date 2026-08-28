"""CLI: `python -m scripts.populate_demo_data`

Fills the already-provisioned "demo" tenant (org skeleton + admin user
already exist via `app.seed.demo_institution.seed_demo_data`) with a small
but complete dataset spanning every feature, so the demo tenant can be used
to click through the whole system: 5 courses with COs and a question bank,
a published curriculum (PEOs/POs/mappings), two terms (one completed with
full marks + attainment data, one ongoing with a partial-weight assessment),
faculty/student users, enrollments, and attainment thresholds.

Idempotent by natural key (course code, term name, user email, ...) — safe
to re-run against an already-populated demo tenant; it fills gaps rather
than duplicating rows.
"""

from __future__ import annotations

import random
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _REPO_ROOT / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.security import hash_password
from app.db.base import WorkflowStatus
from app.db.session import session_scope
from app.db.tenancy import program_schema_name
from app.models.public.institution import Institution
from app.models.tenant.assessments.assessment import (
    Assessment,
    AssessmentQuestion,
    AssessmentType,
    Question,
    QuestionCourseOutcomeMapping,
    Rubric,
    RubricCriterion,
    RubricLevel,
)
from app.models.tenant.assessments.marks import (
    CourseAttainmentConfig,
    ProgramAttainmentConfig,
    StudentMark,
)
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import (
    CourseOffering,
    CourseSection,
    FacultyAssignment,
    StudentEnrollment,
)
from app.models.tenant.identity import (
    FacultyProfile,
    Role,
    StudentProfile,
    User,
    UserRole,
)
from app.models.tenant.mappings.scales import (
    CourseOutcomePOMapping,
    MappingScale,
    MappingScaleLevel,
    ProgramOutcomePEOMapping,
)
from app.models.tenant.obe.improvement import ImprovementPlan
from app.models.tenant.obe.outcomes import (
    PEO,
    CourseOutcome,
    ProgramOutcome,
)
from app.models.tenant.org import (
    AcademicTerm,
    AcademicYear,
    Program,
    ProgramVersion,
)
from app.seed.baete_v3 import seed_baete_v3_framework
from app.services.tenancy import provision_program_schema

DEMO_PASSWORD = "Demo@12345"


def get_or_create(db, model, filters, **extra):
    obj = db.query(model).filter_by(**filters).one_or_none()
    if obj is None:
        obj = model(**filters, **extra)
        db.add(obj)
        db.flush()
    return obj


COURSE_SPECS = [
    (
        "CS101",
        "Introduction to Programming",
        3,
        "Major Core",
        [
            "Write and debug simple procedural programs.",
            "Apply control structures and functions to solve problems.",
            "Use arrays and basic data structures.",
        ],
    ),
    (
        "CS201",
        "Data Structures",
        3,
        "Major Core",
        [
            "Implement linked lists, stacks, and queues.",
            "Analyze time and space complexity of algorithms.",
            "Apply trees and graphs to solve problems.",
        ],
    ),
    (
        "CS301",
        "Database Systems",
        3,
        "Major Core",
        [
            "Design normalized relational schemas.",
            "Write complex SQL queries.",
            "Apply transaction and concurrency concepts.",
        ],
    ),
    (
        "CS310",
        "Computer Networks",
        3,
        "Concentration Elective",
        [
            "Explain the OSI and TCP/IP models.",
            "Analyze routing and congestion control algorithms.",
            "Configure basic network security measures.",
        ],
    ),
    (
        "CS150",
        "Discrete Mathematics",
        3,
        "Science & Math",
        [
            "Apply propositional and predicate logic.",
            "Solve counting and combinatorics problems.",
            "Prove statements using mathematical induction.",
        ],
    ),
]

PEO_STATEMENTS = [
    "Graduates will excel in professional computing careers in industry, academia, or government.",
    "Graduates will pursue lifelong learning and adapt to emerging technologies.",
    "Graduates will demonstrate ethical, socially responsible engineering practice.",
]

PO_STATEMENTS = [
    "Apply knowledge of mathematics, science, and engineering fundamentals.",
    "Identify, formulate, and analyze complex engineering problems.",
    "Design solutions for complex problems, considering public health and safety.",
    "Design and conduct experiments, analyze and interpret data.",
    "Use modern engineering and IT tools with an understanding of their limitations.",
    "Function effectively as an individual and as a member of a team.",
]

FACULTY_SPECS = [
    ("alice.rahman@demo.obevolve.dev", "Dr. Alice Rahman", "EMP-101", "Associate Professor"),
    ("bob.islam@demo.obevolve.dev", "Dr. Bob Islam", "EMP-102", "Assistant Professor"),
    ("carol.chowdhury@demo.obevolve.dev", "Dr. Carol Chowdhury", "EMP-103", "Professor"),
]

STUDENT_NAMES = [
    "Rafi Ahmed", "Nusrat Jahan", "Tanvir Hasan", "Maliha Islam", "Sabbir Rahman",
    "Farhana Akter", "Imran Khan", "Sadia Sultana", "Kamrul Hasan", "Ayesha Siddiqua",
    "Nayeem Chowdhury", "Tasnia Rahman", "Shakib Al Hasan", "Priya Das", "Arif Hossain",
]

# --- A second, smaller program (spec §6/§10 need to show the schema-per-
# program switcher actually switching) — deliberately left with no marks
# entered at all, so the demo tenant also demonstrates what a genuinely
# unassessed program looks like across every attainment/analytics view,
# as a contrast to BSCSE's fully-marked one. ---
BSSE_COURSE_SPECS = [
    (
        "SE101",
        "Software Engineering Fundamentals",
        3,
        "Major Core",
        [
            "Describe the software development lifecycle and common process models.",
            "Write clear software requirements from a problem statement.",
            "Apply basic UML diagrams to model a system.",
        ],
    ),
    (
        "SE201",
        "Software Design Patterns",
        3,
        "Major Core",
        [
            "Identify appropriate design patterns for common design problems.",
            "Apply SOLID principles to refactor a small codebase.",
            "Evaluate trade-offs between competing design approaches.",
        ],
    ),
]

BSSE_PEO_STATEMENTS = [
    "Graduates will design and deliver reliable, maintainable software systems.",
    "Graduates will collaborate effectively in cross-functional engineering teams.",
]

BSSE_PO_STATEMENTS = [
    "Apply software engineering principles to design and build systems.",
    "Communicate technical designs clearly to technical and non-technical audiences.",
    "Work effectively as part of a software development team.",
    "Evaluate the ethical and societal impact of software systems.",
]

BSSE_STUDENT_NAMES = ["Fahim Reza", "Sumaiya Karim", "Rakib Hossain", "Nabila Chowdhury", "Zayan Ahmed"]


def populate(db, *, institution_id, program_id, department_id) -> None:
    year = get_or_create(
        db, AcademicYear, {"label": "2025-2026"},
        start_date=date(2025, 9, 1), end_date=date(2026, 8, 31),
    )
    fall = get_or_create(
        db, AcademicTerm, {"name": "Fall 2025"},
        academic_year_id=year.id, term_type="semester",
        start_date=date(2025, 9, 1), end_date=date(2025, 12, 20),
    )
    spring = get_or_create(
        db, AcademicTerm, {"name": "Spring 2026"},
        academic_year_id=year.id, term_type="semester",
        start_date=date(2026, 1, 5), end_date=date(2026, 5, 15),
    )

    scale = db.query(MappingScale).filter(MappingScale.is_default.is_(True)).one()
    yes_level = (
        db.query(MappingScaleLevel)
        .filter(MappingScaleLevel.mapping_scale_id == scale.id, MappingScaleLevel.label == "Yes")
        .one()
    )

    # --- Curriculum: program version, PEOs, POs, PEO-PO mappings ---
    program_version = get_or_create(
        db, ProgramVersion, {"program_id": program_id, "version_label": "2022"},
        effective_academic_year_id=year.id, status=WorkflowStatus.PUBLISHED,
    )
    peos = []
    for i, statement in enumerate(PEO_STATEMENTS, start=1):
        peo = get_or_create(
            db, PEO, {"program_version_id": program_version.id, "code": f"PEO{i}"},
            statement=statement, sequence=i, status=WorkflowStatus.PUBLISHED,
        )
        peos.append(peo)

    pos = []
    for i, statement in enumerate(PO_STATEMENTS, start=1):
        po = get_or_create(
            db, ProgramOutcome, {"program_version_id": program_version.id, "code": f"PO{i}"},
            statement=statement, sequence=i, status=WorkflowStatus.PUBLISHED,
        )
        pos.append(po)

    for i, po in enumerate(pos):
        peo = peos[i % len(peos)]
        get_or_create(
            db, ProgramOutcomePEOMapping,
            {"program_outcome_id": po.id, "peo_id": peo.id},
            mapping_scale_level_id=yes_level.id,
        )

    # --- Courses, course outcomes, question bank ---
    courses: dict[str, Course] = {}
    course_versions: dict[str, CourseVersion] = {}
    course_outcomes: dict[str, list[CourseOutcome]] = {}
    questions: dict[str, list[Question]] = {}

    for code, title, credits, course_type, co_statements in COURSE_SPECS:
        course = get_or_create(
            db, Course, {"code": code},
            department_id=department_id, title=title,
            credits=Decimal(credits), course_type=course_type,
        )
        courses[code] = course

        cv = get_or_create(
            db, CourseVersion, {"course_id": course.id, "version_label": "2022"},
            effective_academic_year_id=year.id, status=WorkflowStatus.PUBLISHED,
        )
        course_versions[code] = cv

        cos = db.query(CourseOutcome).filter(CourseOutcome.course_version_id == cv.id).all()
        if not cos:
            for i, statement in enumerate(co_statements, start=1):
                co = CourseOutcome(
                    course_version_id=cv.id, code=f"CO{i}", statement=statement,
                    sequence=i, status=WorkflowStatus.PUBLISHED,
                )
                db.add(co)
                cos.append(co)
            db.flush()
        course_outcomes[code] = cos

        # PO mapping: each CO -> 2 POs, spread across the 6 POs
        for j, co in enumerate(cos):
            for k in range(2):
                po = pos[(j * 2 + k) % len(pos)]
                get_or_create(
                    db, CourseOutcomePOMapping,
                    {"course_outcome_id": co.id, "program_outcome_id": po.id},
                    mapping_scale_level_id=yes_level.id,
                )

        qs = db.query(Question).filter(Question.course_version_id == cv.id).all()
        if not qs:
            specs = [
                (cos[0].id, Decimal(20), "short_answer"),
                (cos[1].id, Decimal(30), "essay"),
                (cos[0].id, Decimal(25), "essay"),
                (cos[2].id, Decimal(25), "essay"),
            ]
            for idx, (co_id, marks, qtype) in enumerate(specs, start=1):
                q = Question(
                    course_version_id=cv.id, text=f"{code} sample question {idx}",
                    question_type=qtype, marks=marks, status=WorkflowStatus.PUBLISHED,
                )
                db.add(q)
                db.flush()
                db.add(QuestionCourseOutcomeMapping(question_id=q.id, course_outcome_id=co_id))
                qs.append(q)
        questions[code] = qs

        get_or_create(
            db, CourseAttainmentConfig, {"course_version_id": cv.id},
            min_marks_percent=Decimal(60), min_students_percent=Decimal(60),
        )

    # --- A rubric (unattached — enough to exercise the Rubrics tab) ---
    rubric = get_or_create(
        db, Rubric, {"name": "Project Presentation Rubric"},
        description="Generic rubric for evaluating student presentations.",
    )
    criteria = db.query(RubricCriterion).filter(RubricCriterion.rubric_id == rubric.id).all()
    if not criteria:
        for name, weight in [("Content clarity", Decimal(50)), ("Delivery", Decimal(50))]:
            crit = RubricCriterion(rubric_id=rubric.id, criterion=name, weight=weight)
            db.add(crit)
            db.flush()
            for label, score in [("Excellent", Decimal(100)), ("Satisfactory", Decimal(60))]:
                db.add(RubricLevel(rubric_criterion_id=crit.id, label=label, score=score))

    # --- Faculty ---
    faculty_role = db.query(Role).filter(Role.name == "Faculty").one()
    coordinator_role = db.query(Role).filter(Role.name == "Course Coordinator").one()
    program_coordinator_role = db.query(Role).filter(Role.name == "Program Coordinator").one()

    faculty_users = []
    for email, full_name, emp_code, designation in FACULTY_SPECS:
        user = db.query(User).filter(User.email == email).one_or_none()
        if user is None:
            user = User(email=email, password_hash=hash_password(DEMO_PASSWORD), full_name=full_name)
            db.add(user)
            db.flush()
            db.add(FacultyProfile(user_id=user.id, employee_code=emp_code, designation=designation, department_id=department_id))
            db.add(UserRole(user_id=user.id, role_id=faculty_role.id, scope_type=None, scope_id=None))
        faculty_users.append(user)

    carol = faculty_users[2]
    if not db.query(UserRole).filter(UserRole.user_id == carol.id, UserRole.role_id == coordinator_role.id).count():
        db.add(UserRole(user_id=carol.id, role_id=coordinator_role.id, scope_type=None, scope_id=None))
    if not db.query(UserRole).filter(
        UserRole.user_id == carol.id, UserRole.role_id == program_coordinator_role.id,
        UserRole.scope_type == "program",
    ).count():
        db.add(
            UserRole(
                user_id=carol.id, role_id=program_coordinator_role.id,
                scope_type="program", scope_id=program_id,
            )
        )

    course_faculty = {
        "CS101": faculty_users[0], "CS201": faculty_users[1], "CS301": faculty_users[2],
        "CS310": faculty_users[0], "CS150": faculty_users[1],
    }

    # --- Students ---
    student_role = db.query(Role).filter(Role.name == "Student").one()
    students = []
    for i, name in enumerate(STUDENT_NAMES, start=1):
        email = f"student{i:03d}@demo.obevolve.dev"
        user = db.query(User).filter(User.email == email).one_or_none()
        if user is None:
            user = User(email=email, password_hash=hash_password(DEMO_PASSWORD), full_name=name)
            db.add(user)
            db.flush()
            db.add(
                StudentProfile(
                    user_id=user.id, student_code=f"2022{i:04d}", program_id=program_id,
                    program_version_id=program_version.id, batch_year=2022, status="active",
                )
            )
            db.add(UserRole(user_id=user.id, role_id=student_role.id, scope_type=None, scope_id=None))
        students.append(user)

    # --- Offerings/sections/faculty assignments/enrollments/assessments per term ---
    def build_term(term, *, with_marks: bool) -> dict[str, CourseSection]:
        sections_by_code: dict[str, CourseSection] = {}
        for code in courses:
            cv = course_versions[code]
            offering = get_or_create(
                db, CourseOffering, {"course_version_id": cv.id, "academic_term_id": term.id},
                program_version_id=program_version.id,
            )
            section = get_or_create(
                db, CourseSection, {"course_offering_id": offering.id, "section_code": "A"},
                max_students=40,
            )
            sections_by_code[code] = section
            instructor = course_faculty[code]
            if not db.query(FacultyAssignment).filter(
                FacultyAssignment.course_section_id == section.id,
                FacultyAssignment.faculty_user_id == instructor.id,
            ).count():
                db.add(
                    FacultyAssignment(
                        course_section_id=section.id, faculty_user_id=instructor.id, role="instructor",
                    )
                )

            # A fresh Random per (course, term) rather than drawing from the
            # shared module-level RNG: get_or_create below only calls
            # _rng.uniform() for marks when a row doesn't already exist, so
            # a stateful shared RNG's position would drift between a fresh
            # run and a re-run (which skips already-existing rows) and
            # desync every roster sampled after the first such skip.
            roster = random.Random(f"roster:{code}:{term.name}").sample(students, k=11)
            enrollment_by_student = {}
            for idx, student in enumerate(roster):
                status = "withdrawn" if with_marks and idx == 0 else "enrolled"
                enrollment = get_or_create(
                    db, StudentEnrollment,
                    {"student_user_id": student.id, "course_section_id": section.id},
                    enrollment_status=status,
                )
                enrollment_by_student[student.id] = enrollment

            if with_marks:
                atype_quiz = db.query(AssessmentType).filter(AssessmentType.name == "Quiz").one()
                atype_mid = db.query(AssessmentType).filter(AssessmentType.name == "Midterm").one()
                atype_final = db.query(AssessmentType).filter(AssessmentType.name == "Final Exam").one()
                qbank = questions[code]

                quiz = get_or_create(
                    db, Assessment, {"course_section_id": section.id, "title": "Quiz 1"},
                    academic_term_id=term.id, assessment_type_id=atype_quiz.id,
                    max_marks=Decimal(20), weight=Decimal(20), status=WorkflowStatus.PUBLISHED,
                )
                midterm = get_or_create(
                    db, Assessment, {"course_section_id": section.id, "title": "Midterm"},
                    academic_term_id=term.id, assessment_type_id=atype_mid.id,
                    max_marks=Decimal(30), weight=Decimal(30), status=WorkflowStatus.PUBLISHED,
                )
                final = get_or_create(
                    db, Assessment, {"course_section_id": section.id, "title": "Final Exam"},
                    academic_term_id=term.id, assessment_type_id=atype_final.id,
                    max_marks=Decimal(50), weight=Decimal(50), status=WorkflowStatus.PUBLISHED,
                )

                def attach(assessment, question, sequence):
                    aq = db.query(AssessmentQuestion).filter(
                        AssessmentQuestion.assessment_id == assessment.id,
                        AssessmentQuestion.question_id == question.id,
                    ).one_or_none()
                    if aq is None:
                        aq = AssessmentQuestion(
                            assessment_id=assessment.id, question_id=question.id,
                            marks_allocated=question.marks, sequence=sequence,
                        )
                        db.add(aq)
                        db.flush()
                    return aq

                aq_quiz = attach(quiz, qbank[0], 1)
                aq_mid = attach(midterm, qbank[1], 1)
                aq_final1 = attach(final, qbank[2], 1)
                aq_final2 = attach(final, qbank[3], 2)

                for student in roster:
                    enrollment = enrollment_by_student[student.id]
                    if enrollment.enrollment_status == "withdrawn":
                        continue
                    for aq in (aq_quiz, aq_mid, aq_final1, aq_final2):
                        existing = db.query(StudentMark).filter(
                            StudentMark.assessment_question_id == aq.id,
                            StudentMark.student_enrollment_id == enrollment.id,
                        ).one_or_none()
                        if existing is None:
                            cell_rng = random.Random(f"mark:{enrollment.id}:{aq.id}")
                            pct = cell_rng.uniform(0.45, 0.95)
                            marks = round(float(aq.marks_allocated) * pct * 2) / 2
                            db.add(
                                StudentMark(
                                    assessment_question_id=aq.id,
                                    student_enrollment_id=enrollment.id,
                                    marks_obtained=Decimal(str(marks)),
                                )
                            )
            else:
                atype_quiz = db.query(AssessmentType).filter(AssessmentType.name == "Quiz").one()
                get_or_create(
                    db, Assessment, {"course_section_id": section.id, "title": "Quiz 1"},
                    academic_term_id=term.id, assessment_type_id=atype_quiz.id,
                    max_marks=Decimal(20), weight=Decimal(20), status=WorkflowStatus.PUBLISHED,
                )
        return sections_by_code

    fall_sections = build_term(fall, with_marks=True)
    build_term(spring, with_marks=False)

    # --- Extra coverage: workflow-draft items, improvement plan variety,
    # a second faculty-assignment role, enrollment-status variety, an
    # explicit (non-default) attainment config, and a program-level
    # attainment threshold row — so every status/role/workflow the UI can
    # show has at least one real example in the demo tenant. ---
    cs101_fall = fall_sections["CS101"]
    cs150_fall = fall_sections["CS150"]
    cs310_fall = fall_sections["CS310"]
    cs301_fall = fall_sections["CS301"]

    # A draft CO/Question/Assessment (everything else is published) so the
    # CO-approval and assessment-advance workflows have something to act on.
    cs150_cv = course_versions["CS150"]
    draft_co = get_or_create(
        db, CourseOutcome, {"course_version_id": cs150_cv.id, "code": "CO4"},
        statement="Apply graph theory to model discrete structures.",
        sequence=4, status=WorkflowStatus.DRAFT,
    )
    draft_question = get_or_create(
        db, Question, {"course_version_id": cs150_cv.id, "text": "CS150 draft question (graph theory)"},
        question_type="essay", marks=Decimal(15), status=WorkflowStatus.DRAFT,
    )
    get_or_create(
        db, QuestionCourseOutcomeMapping,
        {"question_id": draft_question.id, "course_outcome_id": draft_co.id},
    )
    atype_test = db.query(AssessmentType).filter(AssessmentType.name == "Class Test").one()
    get_or_create(
        db, Assessment, {"course_section_id": cs101_fall.id, "title": "Class Test 1 (draft)"},
        academic_term_id=fall.id, assessment_type_id=atype_test.id,
        max_marks=Decimal(10), weight=None, status=WorkflowStatus.DRAFT,
    )

    # A second FacultyAssignment role (every existing assignment is
    # "instructor" — add a "coordinator" on the same section) plus a
    # second-instructor scenario so the Faculty Assignments tab shows more
    # than one row per section somewhere.
    if not db.query(FacultyAssignment).filter(
        FacultyAssignment.course_section_id == cs301_fall.id,
        FacultyAssignment.faculty_user_id == carol.id,
        FacultyAssignment.role == "coordinator",
    ).count():
        db.add(
            FacultyAssignment(
                course_section_id=cs301_fall.id, faculty_user_id=carol.id, role="coordinator",
            )
        )

    # Enrollment-status variety beyond enrolled/withdrawn (CS150's Fall
    # roster already has students 1..10 enrolled + 1 withdrawn from
    # build_term above — reuse two of its enrolled students).
    cs150_enrollments = (
        db.query(StudentEnrollment)
        .filter(
            StudentEnrollment.course_section_id == cs150_fall.id,
            StudentEnrollment.enrollment_status == "enrolled",
        )
        .order_by(StudentEnrollment.id)
        .limit(2)
        .all()
    )
    if len(cs150_enrollments) >= 2:
        cs150_enrollments[0].enrollment_status = "completed"
        cs150_enrollments[1].enrollment_status = "failed"

    # wi_treatment variety: every course defaults to "exclude" — flip one
    # to "include" so both configurations are visible somewhere real.
    cs310_config = (
        db.query(CourseAttainmentConfig)
        .filter(CourseAttainmentConfig.course_version_id == course_versions["CS310"].id)
        .one()
    )
    cs310_config.wi_treatment = "include"

    # An explicit (non-default) program-level attainment threshold row —
    # everything else relies on the 60/60 fallback; this one is a real,
    # user-saved config.
    get_or_create(
        db, ProgramAttainmentConfig, {"program_version_id": program_version.id},
        min_po_attainment_percent=Decimal(65),
    )

    # Improvement plans across the full status range (spec §5): the CS301
    # CO2 "Not attained" result (see AttainmentTab) is a real trigger for
    # this workflow. One of each terminal state plus one still "proposed".
    def improvement_plan(course_section_id, course_outcome_id, observation, *, status, **extra):
        plan = get_or_create(
            db, ImprovementPlan,
            {"course_section_id": course_section_id, "problem_observation": observation},
            course_outcome_id=course_outcome_id,
            proposed_action=extra.pop("proposed_action", "revise_assessment"),
            reason=extra.pop("reason", "Identified during end-of-term review."),
            expected_improvement=extra.pop("expected_improvement", "Improve attainment next offering."),
            status=status,
            created_by=carol.id,
            **extra,
        )
        return plan

    cs301_co2 = course_outcomes["CS301"][1]
    improvement_plan(
        cs301_fall.id, cs301_co2.id,
        "Only ~65% of students attained CO2 (SQL query writing) in Fall 2025.",
        status="implemented",
        proposed_action="revise_assessment",
        reason="Midterm SQL questions were too complex relative to lecture coverage.",
        expected_improvement="Raise CO2 attainment to at least 65% next offering.",
        implementation_term_id=spring.id,
        responsible_user_id=carol.id,
        reviewed_by=carol.id,
    )
    cs310_co1 = course_outcomes["CS310"][0]
    improvement_plan(
        cs310_fall.id, cs310_co1.id,
        "Several students struggled to explain the OSI model layers in the final exam.",
        status="proposed",
        proposed_action="additional_materials",
        reason="Lecture slides cover the OSI model briefly; students need worked examples.",
        expected_improvement="Provide a supplementary reading and a worked-example problem set.",
        responsible_user_id=course_faculty["CS310"].id,
    )
    cs150_co3 = course_outcomes["CS150"][2]
    improvement_plan(
        cs150_fall.id, cs150_co3.id,
        "Induction-proof questions had the lowest average score on the final exam.",
        status="rejected",
        proposed_action="new_topic",
        reason="Proposed adding an extra week on induction, but the term schedule has no slack.",
        expected_improvement="N/A — proposal rejected in favor of remedial office hours instead.",
        responsible_user_id=course_faculty["CS150"].id,
        reviewed_by=carol.id,
    )

    db.flush()


def populate_bsse_program(db, *, department_id) -> None:
    """A second program in the same institution, deliberately smaller and
    left with no marks entered — see BSSE_* constants above for why."""
    program = get_or_create(
        db, Program, {"code": "BSSE"},
        name="B.Sc. in Software Engineering", department_id=department_id,
        degree_level="undergraduate",
    )

    year = get_or_create(
        db, AcademicYear, {"label": "2025-2026"},
        start_date=date(2025, 9, 1), end_date=date(2026, 8, 31),
    )
    fall = get_or_create(
        db, AcademicTerm, {"name": "Fall 2025"},
        academic_year_id=year.id, term_type="semester",
        start_date=date(2025, 9, 1), end_date=date(2025, 12, 20),
    )

    scale = db.query(MappingScale).filter(MappingScale.is_default.is_(True)).one()
    yes_level = (
        db.query(MappingScaleLevel)
        .filter(MappingScaleLevel.mapping_scale_id == scale.id, MappingScaleLevel.label == "Yes")
        .one()
    )

    program_version = get_or_create(
        db, ProgramVersion, {"program_id": program.id, "version_label": "2023"},
        effective_academic_year_id=year.id, status=WorkflowStatus.PUBLISHED,
    )
    peos = []
    for i, statement in enumerate(BSSE_PEO_STATEMENTS, start=1):
        peo = get_or_create(
            db, PEO, {"program_version_id": program_version.id, "code": f"PEO{i}"},
            statement=statement, sequence=i, status=WorkflowStatus.PUBLISHED,
        )
        peos.append(peo)

    pos = []
    for i, statement in enumerate(BSSE_PO_STATEMENTS, start=1):
        po = get_or_create(
            db, ProgramOutcome, {"program_version_id": program_version.id, "code": f"PO{i}"},
            statement=statement, sequence=i, status=WorkflowStatus.PUBLISHED,
        )
        pos.append(po)
    for i, po in enumerate(pos):
        get_or_create(
            db, ProgramOutcomePEOMapping,
            {"program_outcome_id": po.id, "peo_id": peos[i % len(peos)].id},
            mapping_scale_level_id=yes_level.id,
        )

    courses: dict[str, Course] = {}
    course_versions: dict[str, CourseVersion] = {}
    for code, title, credits, course_type, co_statements in BSSE_COURSE_SPECS:
        course = get_or_create(
            db, Course, {"code": code},
            department_id=department_id, title=title,
            credits=Decimal(credits), course_type=course_type,
        )
        courses[code] = course
        cv = get_or_create(
            db, CourseVersion, {"course_id": course.id, "version_label": "2023"},
            effective_academic_year_id=year.id, status=WorkflowStatus.PUBLISHED,
        )
        course_versions[code] = cv

        cos = db.query(CourseOutcome).filter(CourseOutcome.course_version_id == cv.id).all()
        if not cos:
            for i, statement in enumerate(co_statements, start=1):
                co = CourseOutcome(
                    course_version_id=cv.id, code=f"CO{i}", statement=statement,
                    sequence=i, status=WorkflowStatus.PUBLISHED,
                )
                db.add(co)
                cos.append(co)
            db.flush()
        for j, co in enumerate(cos):
            po = pos[j % len(pos)]
            get_or_create(
                db, CourseOutcomePOMapping,
                {"course_outcome_id": co.id, "program_outcome_id": po.id},
                mapping_scale_level_id=yes_level.id,
            )

        qs = db.query(Question).filter(Question.course_version_id == cv.id).all()
        if not qs:
            for i, co in enumerate(cos, start=1):
                q = Question(
                    course_version_id=cv.id, text=f"{code} sample question {i}",
                    question_type="essay", marks=Decimal(20), status=WorkflowStatus.PUBLISHED,
                )
                db.add(q)
                db.flush()
                db.add(QuestionCourseOutcomeMapping(question_id=q.id, course_outcome_id=co.id))

    students = []
    for i, name in enumerate(BSSE_STUDENT_NAMES, start=1):
        email = f"bsse.student{i:03d}@demo.obevolve.dev"
        user = db.query(User).filter(User.email == email).one_or_none()
        if user is None:
            user = User(email=email, password_hash=hash_password(DEMO_PASSWORD), full_name=name)
            db.add(user)
            db.flush()
            db.add(
                StudentProfile(
                    user_id=user.id, student_code=f"2023{i:04d}", program_id=program.id,
                    program_version_id=program_version.id, batch_year=2023, status="active",
                )
            )
            student_role = db.query(Role).filter(Role.name == "Student").one()
            db.add(UserRole(user_id=user.id, role_id=student_role.id, scope_type=None, scope_id=None))
        students.append(user)

    instructor = db.query(User).filter(User.email == "alice.rahman@demo.obevolve.dev").one()
    for code, course in courses.items():
        cv = course_versions[code]
        offering = get_or_create(
            db, CourseOffering, {"course_version_id": cv.id, "academic_term_id": fall.id},
            program_version_id=program_version.id,
        )
        section = get_or_create(
            db, CourseSection, {"course_offering_id": offering.id, "section_code": "A"},
            max_students=30,
        )
        if not db.query(FacultyAssignment).filter(
            FacultyAssignment.course_section_id == section.id,
            FacultyAssignment.faculty_user_id == instructor.id,
        ).count():
            db.add(
                FacultyAssignment(
                    course_section_id=section.id, faculty_user_id=instructor.id, role="instructor",
                )
            )
        for student in students:
            get_or_create(
                db, StudentEnrollment,
                {"student_user_id": student.id, "course_section_id": section.id},
                enrollment_status="enrolled",
            )
        atype_quiz = db.query(AssessmentType).filter(AssessmentType.name == "Quiz").one()
        assessment = get_or_create(
            db, Assessment, {"course_section_id": section.id, "title": "Quiz 1"},
            academic_term_id=fall.id, assessment_type_id=atype_quiz.id,
            max_marks=Decimal(20), weight=Decimal(100), status=WorkflowStatus.PUBLISHED,
        )
        q = db.query(Question).filter(Question.course_version_id == cv.id).first()
        if q is not None and not db.query(AssessmentQuestion).filter(
            AssessmentQuestion.assessment_id == assessment.id, AssessmentQuestion.question_id == q.id
        ).count():
            db.add(
                AssessmentQuestion(
                    assessment_id=assessment.id, question_id=q.id,
                    marks_allocated=Decimal(20), sequence=1,
                )
            )
        # Deliberately no StudentMark rows — this program stays "not yet
        # assessed" everywhere (Attainment/PO Attainment/Program Analytics).

    db.flush()


def main() -> None:
    with session_scope() as db:
        inst = db.query(Institution).filter(Institution.slug == "demo").one_or_none()
        if inst is None:
            print("No institution with slug 'demo' found — provision it first.", file=sys.stderr)
            raise SystemExit(1)
        institution_id, schema_name = inst.id, inst.schema_name

    with session_scope(schema_translate_map={None: schema_name}) as db:
        seed_baete_v3_framework(db)
        program = db.query(Program).filter(Program.code == "BSCSE").one()
        program_id, department_id = program.id, program.department_id

    program_schema = program_schema_name(schema_name, "BSCSE")
    print(f"Populating demo data into {schema_name!r} / {program_schema!r} ...")

    with session_scope(schema_translate_map={None: schema_name, "program": program_schema}) as db:
        populate(db, institution_id=institution_id, program_id=program_id, department_id=department_id)

    bsse_program_schema = provision_program_schema(schema_name, "BSSE")
    print(f"Populating a second program into {bsse_program_schema!r} ...")
    with session_scope(
        schema_translate_map={None: schema_name, "program": bsse_program_schema}
    ) as db:
        populate_bsse_program(db, department_id=department_id)

    print("Done.")


if __name__ == "__main__":
    main()
