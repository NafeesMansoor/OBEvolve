"""Course delivery (offerings/sections/faculty assignments/enrollment) and
student profile + curriculum alignment (DATABASE_PLAN.md §C).

Reads require `*.view`, writes require `*.manage` — never a role-name check
(ARCHITECTURE.md §3). Marks entry/gradebook is a separate, later feature —
out of scope here (see `app.models.tenant.assessments` README).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.courses.delivery import (
    CourseOffering,
    CourseSection,
    FacultyAssignment,
    StudentEnrollment,
)
from app.models.tenant.identity import StudentProfile, User
from app.schemas.academic import (
    CourseOfferingCreate,
    CourseOfferingRead,
    CourseSectionCreate,
    CourseSectionRead,
    FacultyAssignmentCreate,
    FacultyAssignmentRead,
    StudentAlignmentUpdate,
    StudentCreate,
    StudentEnrollmentCreate,
    StudentEnrollmentRead,
    StudentRead,
)
from app.services.audit import write_audit_log
from app.services.rbac import require_permission

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: uuid.UUID, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


def _student_read(user: User, profile: StudentProfile) -> StudentRead:
    return StudentRead(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        student_code=profile.student_code,
        program_id=profile.program_id,
        program_version_id=profile.program_version_id,
        batch_year=profile.batch_year,
        status=profile.status,
    )


# --- Course offerings ---
@router.post(
    "/course-offerings", response_model=CourseOfferingRead, status_code=status.HTTP_201_CREATED
)
def create_course_offering(
    payload: CourseOfferingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("section.manage")),
) -> CourseOffering:
    offering = CourseOffering(**payload.model_dump())
    db.add(offering)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_offering.created",
        entity_type="CourseOffering",
        entity_id=offering.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return offering


@router.get("/course-offerings", response_model=list[CourseOfferingRead])
def list_course_offerings(
    course_version_id: uuid.UUID | None = Query(default=None),
    academic_term_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("section.view")),
) -> list[CourseOffering]:
    query = db.query(CourseOffering)
    if course_version_id is not None:
        query = query.filter(CourseOffering.course_version_id == course_version_id)
    if academic_term_id is not None:
        query = query.filter(CourseOffering.academic_term_id == academic_term_id)
    return query.order_by(CourseOffering.created_at.desc()).all()


@router.get("/course-offerings/{offering_id}", response_model=CourseOfferingRead)
def get_course_offering(
    offering_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("section.view")),
) -> CourseOffering:
    return _get_or_404(db, CourseOffering, offering_id, "Course offering")


@router.patch("/course-offerings/{offering_id}", response_model=CourseOfferingRead)
def update_course_offering(
    offering_id: uuid.UUID,
    payload: CourseOfferingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("section.manage")),
) -> CourseOffering:
    offering = _get_or_404(db, CourseOffering, offering_id, "Course offering")
    previous_value = {
        "course_version_id": str(offering.course_version_id),
        "academic_term_id": str(offering.academic_term_id),
        "program_version_id": str(offering.program_version_id)
        if offering.program_version_id
        else None,
    }
    for field, value in payload.model_dump().items():
        setattr(offering, field, value)
    db.add(offering)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_offering.updated",
        entity_type="CourseOffering",
        entity_id=offering.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return offering


@router.delete("/course-offerings/{offering_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_offering(
    offering_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("section.manage")),
) -> None:
    offering = _get_or_404(db, CourseOffering, offering_id, "Course offering")
    db.delete(offering)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_offering.deleted",
        entity_type="CourseOffering",
        entity_id=offering_id,
        **get_request_context(request),
    )


# --- Course sections ---
@router.post("/sections", response_model=CourseSectionRead, status_code=status.HTTP_201_CREATED)
def create_course_section(
    payload: CourseSectionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("section.manage")),
) -> CourseSection:
    _get_or_404(db, CourseOffering, payload.course_offering_id, "Course offering")
    section = CourseSection(**payload.model_dump())
    db.add(section)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_section.created",
        entity_type="CourseSection",
        entity_id=section.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return section


@router.get("/sections", response_model=list[CourseSectionRead])
def list_course_sections(
    course_offering_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("section.view")),
) -> list[CourseSection]:
    query = db.query(CourseSection)
    if course_offering_id is not None:
        query = query.filter(CourseSection.course_offering_id == course_offering_id)
    return query.order_by(CourseSection.section_code).all()


@router.get("/sections/{section_id}", response_model=CourseSectionRead)
def get_course_section(
    section_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("section.view")),
) -> CourseSection:
    return _get_or_404(db, CourseSection, section_id, "Course section")


@router.patch("/sections/{section_id}", response_model=CourseSectionRead)
def update_course_section(
    section_id: uuid.UUID,
    payload: CourseSectionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("section.manage")),
) -> CourseSection:
    section = _get_or_404(db, CourseSection, section_id, "Course section")
    previous_value = {
        "course_offering_id": str(section.course_offering_id),
        "section_code": section.section_code,
        "max_students": section.max_students,
    }
    _get_or_404(db, CourseOffering, payload.course_offering_id, "Course offering")
    for field, value in payload.model_dump().items():
        setattr(section, field, value)
    db.add(section)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_section.updated",
        entity_type="CourseSection",
        entity_id=section.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return section


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_section(
    section_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("section.manage")),
) -> None:
    section = _get_or_404(db, CourseSection, section_id, "Course section")
    db.delete(section)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_section.deleted",
        entity_type="CourseSection",
        entity_id=section_id,
        **get_request_context(request),
    )


# --- Faculty assignments ---
@router.post(
    "/faculty-assignments",
    response_model=FacultyAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_faculty_assignment(
    payload: FacultyAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("section.manage")),
) -> FacultyAssignment:
    _get_or_404(db, CourseSection, payload.course_section_id, "Course section")
    _get_or_404(db, User, payload.faculty_user_id, "Faculty user")
    assignment = FacultyAssignment(**payload.model_dump())
    db.add(assignment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="faculty_assignment.created",
        entity_type="FacultyAssignment",
        entity_id=assignment.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return assignment


@router.get("/faculty-assignments", response_model=list[FacultyAssignmentRead])
def list_faculty_assignments(
    course_section_id: uuid.UUID | None = Query(default=None),
    faculty_user_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("section.view")),
) -> list[FacultyAssignment]:
    query = db.query(FacultyAssignment)
    if course_section_id is not None:
        query = query.filter(FacultyAssignment.course_section_id == course_section_id)
    if faculty_user_id is not None:
        query = query.filter(FacultyAssignment.faculty_user_id == faculty_user_id)
    return query.order_by(FacultyAssignment.created_at.desc()).all()


@router.delete("/faculty-assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faculty_assignment(
    assignment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("section.manage")),
) -> None:
    assignment = _get_or_404(db, FacultyAssignment, assignment_id, "Faculty assignment")
    db.delete(assignment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="faculty_assignment.deleted",
        entity_type="FacultyAssignment",
        entity_id=assignment_id,
        **get_request_context(request),
    )


# --- Student enrollment ---
@router.post(
    "/enrollments", response_model=StudentEnrollmentRead, status_code=status.HTTP_201_CREATED
)
def create_enrollment(
    payload: StudentEnrollmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("student.manage")),
) -> StudentEnrollment:
    _get_or_404(db, User, payload.student_user_id, "Student user")
    _get_or_404(db, CourseSection, payload.course_section_id, "Course section")
    enrollment = StudentEnrollment(**payload.model_dump())
    db.add(enrollment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="student_enrollment.created",
        entity_type="StudentEnrollment",
        entity_id=enrollment.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return enrollment


@router.get("/enrollments", response_model=list[StudentEnrollmentRead])
def list_enrollments(
    course_section_id: uuid.UUID | None = Query(default=None),
    student_user_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("student.view")),
) -> list[StudentEnrollment]:
    query = db.query(StudentEnrollment)
    if course_section_id is not None:
        query = query.filter(StudentEnrollment.course_section_id == course_section_id)
    if student_user_id is not None:
        query = query.filter(StudentEnrollment.student_user_id == student_user_id)
    return query.order_by(StudentEnrollment.enrolled_at.desc()).all()


@router.patch("/enrollments/{enrollment_id}", response_model=StudentEnrollmentRead)
def update_enrollment_status(
    enrollment_id: uuid.UUID,
    enrollment_status: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("student.manage")),
) -> StudentEnrollment:
    enrollment = _get_or_404(db, StudentEnrollment, enrollment_id, "Enrollment")
    previous_value = {"enrollment_status": enrollment.enrollment_status}
    enrollment.enrollment_status = enrollment_status
    db.add(enrollment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="student_enrollment.status_changed",
        entity_type="StudentEnrollment",
        entity_id=enrollment.id,
        previous_value=previous_value,
        new_value={"enrollment_status": enrollment_status},
        **get_request_context(request),
    )
    return enrollment


@router.delete("/enrollments/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(
    enrollment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("student.manage")),
) -> None:
    enrollment = _get_or_404(db, StudentEnrollment, enrollment_id, "Enrollment")
    db.delete(enrollment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="student_enrollment.deleted",
        entity_type="StudentEnrollment",
        entity_id=enrollment_id,
        **get_request_context(request),
    )


# --- Students (User + StudentProfile, curriculum alignment) ---
@router.post("/students", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("student.manage")),
) -> StudentRead:
    if db.query(User).filter(User.email == payload.email).one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()

    profile = StudentProfile(
        user_id=user.id,
        student_code=payload.student_code,
        program_id=payload.program_id,
        program_version_id=payload.program_version_id,
        batch_year=payload.batch_year,
        status="active",
    )
    db.add(profile)
    db.flush()

    write_audit_log(
        db,
        user_id=current_user.id,
        action="student.created",
        entity_type="StudentProfile",
        entity_id=user.id,
        new_value={
            "email": payload.email,
            "full_name": payload.full_name,
            "student_code": payload.student_code,
            "program_id": str(payload.program_id) if payload.program_id else None,
            "program_version_id": str(payload.program_version_id)
            if payload.program_version_id
            else None,
            "batch_year": payload.batch_year,
        },
        **get_request_context(request),
    )
    return _student_read(user, profile)


@router.get("/students", response_model=list[StudentRead])
def list_students(
    program_id: uuid.UUID | None = Query(default=None),
    program_version_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("student.view")),
) -> list[StudentRead]:
    query = db.query(StudentProfile)
    if program_id is not None:
        query = query.filter(StudentProfile.program_id == program_id)
    if program_version_id is not None:
        query = query.filter(StudentProfile.program_version_id == program_version_id)
    profiles = query.all()
    users_by_id = {u.id: u for u in db.query(User).filter(
        User.id.in_([p.user_id for p in profiles])
    ).all()} if profiles else {}
    return [
        _student_read(users_by_id[p.user_id], p)
        for p in profiles
        if p.user_id in users_by_id
    ]


@router.get("/students/{user_id}", response_model=StudentRead)
def get_student(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("student.view")),
) -> StudentRead:
    profile = _get_or_404(db, StudentProfile, user_id, "Student")
    user = _get_or_404(db, User, user_id, "Student")
    return _student_read(user, profile)


@router.patch("/students/{user_id}", response_model=StudentRead)
def update_student_alignment(
    user_id: uuid.UUID,
    payload: StudentAlignmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("student.manage")),
) -> StudentRead:
    profile = _get_or_404(db, StudentProfile, user_id, "Student")
    user = _get_or_404(db, User, user_id, "Student")

    previous_value = {
        "program_id": str(profile.program_id) if profile.program_id else None,
        "program_version_id": str(profile.program_version_id)
        if profile.program_version_id
        else None,
        "batch_year": profile.batch_year,
        "status": profile.status,
    }
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)
    db.add(profile)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="student.curriculum_alignment_updated",
        entity_type="StudentProfile",
        entity_id=user_id,
        previous_value=previous_value,
        new_value={
            k: (str(v) if isinstance(v, uuid.UUID) else v) for k, v in updates.items()
        },
        **get_request_context(request),
    )
    return _student_read(user, profile)
