"""Seeds the ULAB CSE program (org structure, PEOs/POs, and the full course
catalog with course outcomes) into a tenant schema, from
`app/seed/data/ulab_cse_curriculum.json` (extracted verbatim from ULAB's
published CSE curriculum document).

Idempotent — every entity is looked up by its natural key before insert
(same pattern as `app.seed.default_roles`), so re-running this against an
already-seeded tenant creates nothing new.

Per docs/adr/0002-framework-aware-outcomes.md, `program_outcomes.code` /
`.statement` are kept exactly as ULAB published them (e.g. "PLO1", wording
that may differ from BAETE's own "PO1") — never rewritten to match the
framework's codes/wording. `framework_po_id` is the only link between the
two, set by outcome *slot* (sequence position), not text.

No CO-PO or PEO-PO mapping rows are created here — see
`app.models.tenant.mappings` and DATABASE_PLAN.md §E: that data was
deliberately excluded from curriculum-document extraction.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.tenant.accreditation import AccreditationFramework, FrameworkPO
from app.models.tenant.courses import Course, CourseVersion
from app.models.tenant.obe import PEO, CourseOutcome, ProgramOutcome
from app.models.tenant.org import AcademicYear, Campus, Department, Program, ProgramVersion, School
from app.seed.mapping_defaults import seed_default_mapping_scale

_DATA_PATH = Path(__file__).parent / "data" / "ulab_cse_curriculum.json"

_TITLE_SPLIT_RE = re.compile(r"\s[-–]\s")  # " - " or " – " (en dash)
_STOPWORDS = {"of", "in", "and", "the", "for", "&"}


def _load_data() -> dict:
    with _DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _derive_program_code(degree_name: str) -> str:
    """e.g. "Bachelor of Science in Computer Science and Engineering" -> "BSCSE"."""
    words = [w for w in re.split(r"\s+", degree_name) if w.lower() not in _STOPWORDS]
    return "".join(w[0].upper() for w in words if w)


def _derive_short_code(name: str) -> str:
    """e.g. "School of Science and Engineering" -> "SSE"."""
    words = [w for w in re.split(r"\s+", name) if w.lower() not in _STOPWORDS]
    return "".join(w[0].upper() for w in words if w)


def _split_plo_title(statement: str) -> tuple[str | None, str]:
    """ULAB PLOs are formatted "Category - Statement"; split on the first
    "-"/"–". Falls back to (None, statement) if no separator is found."""
    parts = _TITLE_SPLIT_RE.split(statement, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, statement.strip()


def _parse_credits(raw: str) -> Decimal:
    """"1" -> Decimal("1.00"); "3.0" -> Decimal("3.00"); "3+1" (lecture+lab)
    -> Decimal("4.00") (summed total credit hours — a judgment call, since
    the source keeps lecture/lab as one combined course entry)."""
    parts = raw.split("+")
    total = sum((Decimal(p.strip()) for p in parts), Decimal("0"))
    return total.quantize(Decimal("0.01"))


def _get_or_create_campus(
    db: Session, *, institution_id: uuid.UUID, name: str, code: str
) -> Campus:
    existing = db.query(Campus).filter(Campus.code == code).one_or_none()
    if existing is not None:
        return existing
    campus = Campus(institution_id=institution_id, name=name, code=code, is_active=True)
    db.add(campus)
    db.flush()
    return campus


def _get_or_create_school(db: Session, *, campus_id: uuid.UUID, name: str, code: str) -> School:
    existing = (
        db.query(School).filter(School.campus_id == campus_id, School.code == code).one_or_none()
    )
    if existing is not None:
        return existing
    school = School(campus_id=campus_id, name=name, code=code, is_active=True)
    db.add(school)
    db.flush()
    return school


def _get_or_create_department(
    db: Session, *, school_id: uuid.UUID, name: str, code: str
) -> Department:
    existing = (
        db.query(Department)
        .filter(Department.school_id == school_id, Department.code == code)
        .one_or_none()
    )
    if existing is not None:
        return existing
    department = Department(school_id=school_id, name=name, code=code, is_active=True)
    db.add(department)
    db.flush()
    return department


def _get_or_create_academic_year(db: Session, *, label: str) -> AcademicYear:
    existing = db.query(AcademicYear).filter(AcademicYear.label == label).one_or_none()
    if existing is not None:
        return existing
    # The curriculum year is a nominal label, not a real term calendar yet
    # (no academic_terms exist for a fresh tenant) — use the calendar year's
    # own bounds as a reasonable placeholder.
    year_int = int(label)
    academic_year = AcademicYear(
        label=label,
        start_date=date(year_int, 1, 1),
        end_date=date(year_int, 12, 31),
        is_active=True,
    )
    db.add(academic_year)
    db.flush()
    return academic_year


def seed_ulab_cse_program(
    db: Session, *, institution_id: uuid.UUID, framework: AccreditationFramework | None
) -> Program:
    """Create (or return the existing) ULAB CSE program, fully seeded:
    org structure, one published ProgramVersion with PEOs/POs, and the full
    127-course catalog (with CourseOutcomes for the ~38 courses that have
    them). Idempotent at every entity level."""
    data = _load_data()
    program_data = data["program"]

    # Always ensure the tenant-wide default mapping scale exists, regardless
    # of whether the program itself is new (DATABASE_PLAN.md §E).
    seed_default_mapping_scale(db)

    campus = _get_or_create_campus(
        db, institution_id=institution_id, name="Main Campus", code="MAIN"
    )
    school = _get_or_create_school(
        db,
        campus_id=campus.id,
        name=program_data["faculty"],
        code=_derive_short_code(program_data["faculty"]),
    )
    department = _get_or_create_department(
        db,
        school_id=school.id,
        name=program_data["department"],
        code=_derive_short_code(program_data["department"]),
    )

    program_code = _derive_program_code(program_data["degree_name"])
    program = (
        db.query(Program)
        .filter(Program.department_id == department.id, Program.code == program_code)
        .one_or_none()
    )
    if program is None:
        program = Program(
            department_id=department.id,
            name=program_data["degree_name"],
            code=program_code,
            degree_level="undergraduate",
            is_active=True,
        )
        db.add(program)
        db.flush()

    curriculum_year = program_data["curriculum_year"]
    academic_year = _get_or_create_academic_year(db, label=curriculum_year)

    program_version = (
        db.query(ProgramVersion)
        .filter(
            ProgramVersion.program_id == program.id,
            ProgramVersion.version_label == curriculum_year,
        )
        .one_or_none()
    )
    if program_version is None:
        program_version = ProgramVersion(
            program_id=program.id,
            version_label=curriculum_year,
            effective_academic_year_id=academic_year.id,
        )
        db.add(program_version)
        db.flush()

    _seed_peos(db, program_version_id=program_version.id, peos_data=data["peos"])
    _seed_program_outcomes(
        db, program_version_id=program_version.id, plos_data=data["plos"], framework=framework
    )
    _seed_courses(
        db,
        department_id=department.id,
        curriculum_year=curriculum_year,
        courses_data=data["courses"],
    )

    db.flush()
    return program


def _seed_peos(db: Session, *, program_version_id: uuid.UUID, peos_data: list[dict]) -> None:
    existing_codes = {
        peo.code
        for peo in db.query(PEO).filter(PEO.program_version_id == program_version_id).all()
    }
    for i, peo_data in enumerate(peos_data, start=1):
        if peo_data["code"] in existing_codes:
            continue
        db.add(
            PEO(
                program_version_id=program_version_id,
                code=peo_data["code"],
                statement=peo_data["statement"],
                sequence=i,
                is_active=True,
            )
        )
    db.flush()


def _seed_program_outcomes(
    db: Session,
    *,
    program_version_id: uuid.UUID,
    plos_data: list[dict],
    framework: AccreditationFramework | None,
) -> None:
    framework_pos: list[FrameworkPO] = []
    if framework is not None:
        framework_pos = (
            db.query(FrameworkPO)
            .filter(FrameworkPO.framework_id == framework.id)
            .order_by(FrameworkPO.sequence)
            .all()
        )

    existing_codes = {
        po.code
        for po in db.query(ProgramOutcome)
        .filter(ProgramOutcome.program_version_id == program_version_id)
        .all()
    }
    for i, plo_data in enumerate(plos_data, start=1):
        if plo_data["code"] in existing_codes:
            continue
        title, statement = _split_plo_title(plo_data["statement"])
        # Link by outcome slot/sequence position (ULAB's i-th PLO <-> BAETE's
        # i-th PO), never by text match — docs/adr/0002-framework-aware-outcomes.md.
        framework_po_id = framework_pos[i - 1].id if i - 1 < len(framework_pos) else None
        db.add(
            ProgramOutcome(
                program_version_id=program_version_id,
                framework_po_id=framework_po_id,
                code=plo_data["code"],
                title=title,
                statement=statement,
                sequence=i,
                is_active=True,
            )
        )
    db.flush()


def _seed_courses(
    db: Session, *, department_id: uuid.UUID, curriculum_year: str, courses_data: list[dict]
) -> None:
    for course_data in courses_data:
        code = course_data["course_code"]
        course = db.query(Course).filter(Course.code == code).one_or_none()
        if course is None:
            # `description` is the closest matching column in the Phase 2/3
            # catalog schema (DATABASE_PLAN.md §C) for the source's
            # `course_objective` text — populate it rather than discard real
            # extracted data. `course_content` (syllabus topic list) has no
            # matching column and stays unpersisted; that's a smaller loss
            # (less critical than the objective) and adding a column for it
            # is a schema decision for a later pass, not this one.
            course = Course(
                department_id=department_id,
                code=code,
                title=course_data["course_title"],
                description=course_data.get("course_objective"),
                credits=_parse_credits(course_data["credit"]),
                course_type=course_data.get("category"),
                is_active=True,
            )
            db.add(course)
            db.flush()

        course_version = (
            db.query(CourseVersion)
            .filter(
                CourseVersion.course_id == course.id,
                CourseVersion.version_label == curriculum_year,
            )
            .one_or_none()
        )
        if course_version is None:
            course_version = CourseVersion(
                course_id=course.id,
                version_label=curriculum_year,
                effective_academic_year_id=None,
            )
            db.add(course_version)
            db.flush()

        outcomes = course_data.get("course_outcomes") or []
        if not outcomes:
            continue
        existing_co_codes = {
            co.code
            for co in db.query(CourseOutcome)
            .filter(CourseOutcome.course_version_id == course_version.id)
            .all()
        }
        for i, co_data in enumerate(outcomes, start=1):
            if co_data["code"] in existing_co_codes:
                continue
            db.add(
                CourseOutcome(
                    course_version_id=course_version.id,
                    code=co_data["code"],
                    statement=co_data["statement"],
                    sequence=i,
                    is_active=True,
                )
            )
    db.flush()
