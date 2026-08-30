"""CRUD for assessment definition (DATABASE_PLAN.md §F): assessment types,
rubrics, questions, assessments. Marks entry/gradebook is a separate, later
feature — out of scope here (see `app.models.tenant.assessments` README).

Type listing is `assessment.view`; creating custom types is `assessment.create`;
question/assessment workflow-advance is `assessment.approve` — matching the
shared workflow shape used elsewhere (ARCHITECTURE.md §4).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.base import WorkflowStatus
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.assessments import (
    Assessment,
    AssessmentDocument,
    AssessmentQuestion,
    AssessmentQuestionProgramOutcomeMapping,
    AssessmentType,
    Question,
    QuestionBloomMapping,
    QuestionCourseOutcomeMapping,
    Rubric,
    RubricCriterion,
    RubricLevel,
)
from app.models.tenant.identity import User
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentDocumentDeadlineExtend,
    AssessmentDocumentRead,
    AssessmentDocumentReview,
    AssessmentQuestionCreate,
    AssessmentQuestionProgramOutcomeMappingCreate,
    AssessmentQuestionProgramOutcomeMappingRead,
    AssessmentQuestionRead,
    AssessmentRead,
    AssessmentTypeCreate,
    AssessmentTypeRead,
    PendingAssessmentDocument,
    QuestionBloomMappingCreate,
    QuestionBloomMappingRead,
    QuestionCourseOutcomeMappingCreate,
    QuestionCourseOutcomeMappingRead,
    QuestionCreate,
    QuestionRead,
    RubricCreate,
    RubricCriterionCreate,
    RubricCriterionRead,
    RubricLevelCreate,
    RubricLevelRead,
    RubricRead,
)
from app.schemas.attainment import AssessmentWeightSummary
from app.services.audit import write_audit_log
from app.services.faculty_scope import (
    ensure_assigned_to_section,
    ensure_section_access,
    filter_to_my_sections,
)
from app.services.rbac import get_program_scoped_db, require_permission
from app.services.storage import delete_upload, read_upload, save_upload

# Singleton slots: at most one row per (assessment_id, document_type) —
# re-uploading replaces it in place. Repeatable slots (_MULTI_DOCUMENT_TYPES):
# any number of rows — uploading always adds a new one, reviewed/deleted
# individually. See AssessmentDocument's docstring.
_SINGLETON_DOCUMENT_TYPES = {
    "question_paper",
    "moderation_form",
    "compliance_form",
    "script_highest",
    "script_lowest",
    "script_median",
    "problem_definition",
}
_MULTI_DOCUMENT_TYPES = {"marked_rubric_sample", "project_report"}
_DOCUMENT_TYPES = _SINGLETON_DOCUMENT_TYPES | _MULTI_DOCUMENT_TYPES

# document_type -> minimum count required, keyed by which AssessmentType flag
# gates it. Not enforced server-side as a hard block (a Program Administrator
# can always see + extend an incomplete assessment); exposed via
# GET .../documents so the frontend can render completeness/deadline banners.
_EXAM_REQUIRED_DOCUMENT_TYPES: dict[str, int] = {
    "question_paper": 1,
    "moderation_form": 1,
    "compliance_form": 1,
    "script_highest": 1,
    "script_lowest": 1,
    "script_median": 1,
}
_CEP_REQUIRED_DOCUMENT_TYPES: dict[str, int] = {
    "problem_definition": 1,
    "marked_rubric_sample": 1,
    "project_report": 3,
}

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: uuid.UUID, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


# --- Assessment types ---
@router.post(
    "/types", response_model=AssessmentTypeRead, status_code=status.HTTP_201_CREATED
)
def create_assessment_type(
    payload: AssessmentTypeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> AssessmentType:
    assessment_type = AssessmentType(name=payload.name, is_custom=True)
    db.add(assessment_type)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment_type.created",
        entity_type="AssessmentType",
        entity_id=assessment_type.id,
        new_value={"name": payload.name, "is_custom": True},
        **get_request_context(request),
    )
    return assessment_type


@router.get("/types", response_model=list[AssessmentTypeRead])
def list_assessment_types(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[AssessmentType]:
    return db.query(AssessmentType).order_by(AssessmentType.name).all()


@router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment_type(
    type_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> None:
    assessment_type = _get_or_404(db, AssessmentType, type_id, "Assessment type")
    if not assessment_type.is_custom:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a default assessment type"
        )
    db.delete(assessment_type)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment_type.deleted",
        entity_type="AssessmentType",
        entity_id=type_id,
        **get_request_context(request),
    )


# --- Rubrics ---
@router.post("/rubrics", response_model=RubricRead, status_code=status.HTTP_201_CREATED)
def create_rubric(
    payload: RubricCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> Rubric:
    rubric = Rubric(**payload.model_dump())
    db.add(rubric)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="rubric.created",
        entity_type="Rubric",
        entity_id=rubric.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return rubric


@router.get("/rubrics", response_model=list[RubricRead])
def list_rubrics(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[Rubric]:
    return db.query(Rubric).order_by(Rubric.name).all()


@router.get("/rubrics/{rubric_id}", response_model=RubricRead)
def get_rubric(
    rubric_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> Rubric:
    return _get_or_404(db, Rubric, rubric_id, "Rubric")


@router.delete("/rubrics/{rubric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rubric(
    rubric_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> None:
    rubric = _get_or_404(db, Rubric, rubric_id, "Rubric")
    db.delete(rubric)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="rubric.deleted",
        entity_type="Rubric",
        entity_id=rubric_id,
        **get_request_context(request),
    )


# --- Rubric criteria ---
@router.post(
    "/rubric-criteria", response_model=RubricCriterionRead, status_code=status.HTTP_201_CREATED
)
def create_rubric_criterion(
    payload: RubricCriterionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> RubricCriterion:
    _get_or_404(db, Rubric, payload.rubric_id, "Rubric")
    criterion = RubricCriterion(**payload.model_dump())
    db.add(criterion)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="rubric_criterion.created",
        entity_type="RubricCriterion",
        entity_id=criterion.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return criterion


@router.get("/rubric-criteria", response_model=list[RubricCriterionRead])
def list_rubric_criteria(
    rubric_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[RubricCriterion]:
    query = db.query(RubricCriterion)
    if rubric_id is not None:
        query = query.filter(RubricCriterion.rubric_id == rubric_id)
    return query.all()


@router.delete("/rubric-criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rubric_criterion(
    criterion_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> None:
    criterion = _get_or_404(db, RubricCriterion, criterion_id, "Rubric criterion")
    db.delete(criterion)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="rubric_criterion.deleted",
        entity_type="RubricCriterion",
        entity_id=criterion_id,
        **get_request_context(request),
    )


# --- Rubric levels ---
@router.post(
    "/rubric-levels", response_model=RubricLevelRead, status_code=status.HTTP_201_CREATED
)
def create_rubric_level(
    payload: RubricLevelCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> RubricLevel:
    _get_or_404(db, RubricCriterion, payload.rubric_criterion_id, "Rubric criterion")
    level = RubricLevel(**payload.model_dump())
    db.add(level)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="rubric_level.created",
        entity_type="RubricLevel",
        entity_id=level.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return level


@router.get("/rubric-levels", response_model=list[RubricLevelRead])
def list_rubric_levels(
    rubric_criterion_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[RubricLevel]:
    query = db.query(RubricLevel)
    if rubric_criterion_id is not None:
        query = query.filter(RubricLevel.rubric_criterion_id == rubric_criterion_id)
    return query.all()


@router.delete("/rubric-levels/{level_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rubric_level(
    level_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> None:
    level = _get_or_404(db, RubricLevel, level_id, "Rubric level")
    db.delete(level)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="rubric_level.deleted",
        entity_type="RubricLevel",
        entity_id=level_id,
        **get_request_context(request),
    )


# --- Questions ---
@router.post("/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(
    payload: QuestionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> Question:
    question = Question(
        **payload.model_dump(), status=WorkflowStatus.DRAFT
    )
    db.add(question)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="question.created",
        entity_type="Question",
        entity_id=question.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return question


@router.get("/questions", response_model=list[QuestionRead])
def list_questions(
    course_version_id: uuid.UUID | None = Query(default=None),
    is_globally_shared: bool | None = Query(
        default=None,
        description="Question Bank search (spec §16-17): filter to questions "
        "explicitly shared for reuse across sections/terms.",
    ),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[Question]:
    query = db.query(Question)
    if course_version_id is not None:
        query = query.filter(Question.course_version_id == course_version_id)
    if is_globally_shared is not None:
        query = query.filter(Question.is_globally_shared.is_(is_globally_shared))
    return query.order_by(Question.created_at.desc()).all()


@router.get("/questions/{question_id}", response_model=QuestionRead)
def get_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> Question:
    return _get_or_404(db, Question, question_id, "Question")


@router.patch("/questions/{question_id}", response_model=QuestionRead)
def update_question(
    question_id: uuid.UUID,
    payload: QuestionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> Question:
    question = _get_or_404(db, Question, question_id, "Question")
    previous_value = {
        "text": question.text,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "marks": str(question.marks),
        "topic": question.topic,
    }
    for field, value in payload.model_dump().items():
        setattr(question, field, value)
    db.add(question)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="question.updated",
        entity_type="Question",
        entity_id=question.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> None:
    question = _get_or_404(db, Question, question_id, "Question")
    db.delete(question)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="question.deleted",
        entity_type="Question",
        entity_id=question_id,
        **get_request_context(request),
    )


_NEXT_STATUS: dict[WorkflowStatus, WorkflowStatus] = {
    WorkflowStatus.DRAFT: WorkflowStatus.SUBMITTED,
    WorkflowStatus.SUBMITTED: WorkflowStatus.REVIEWED,
    WorkflowStatus.REVIEWED: WorkflowStatus.APPROVED,
    WorkflowStatus.APPROVED: WorkflowStatus.PUBLISHED,
}


@router.post("/questions/{question_id}/advance", response_model=QuestionRead)
def advance_question(
    question_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.approve")),
) -> Question:
    question = _get_or_404(db, Question, question_id, "Question")
    current_status = WorkflowStatus(question.status)
    next_status = _NEXT_STATUS.get(current_status)
    if next_status is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Question in status {current_status.value!r} cannot be advanced further.",
        )
    previous_value = {"status": current_status.value}
    question.status = next_status
    if next_status == WorkflowStatus.APPROVED:
        question.reviewer_id = current_user.id
    db.add(question)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="question.status_changed",
        entity_type="Question",
        entity_id=question.id,
        previous_value=previous_value,
        new_value={"status": next_status.value},
        **get_request_context(request),
    )
    return question


# --- Question CO / Bloom mappings ---
@router.post(
    "/question-co-mappings",
    response_model=QuestionCourseOutcomeMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_question_co_mapping(
    payload: QuestionCourseOutcomeMappingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> QuestionCourseOutcomeMapping:
    _get_or_404(db, Question, payload.question_id, "Question")
    mapping = QuestionCourseOutcomeMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="question_co_mapping.created",
        entity_type="QuestionCourseOutcomeMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get("/question-co-mappings", response_model=list[QuestionCourseOutcomeMappingRead])
def list_question_co_mappings(
    question_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[QuestionCourseOutcomeMapping]:
    query = db.query(QuestionCourseOutcomeMapping)
    if question_id is not None:
        query = query.filter(QuestionCourseOutcomeMapping.question_id == question_id)
    return query.all()


@router.delete("/question-co-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question_co_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> None:
    mapping = _get_or_404(db, QuestionCourseOutcomeMapping, mapping_id, "Question-CO mapping")
    db.delete(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="question_co_mapping.deleted",
        entity_type="QuestionCourseOutcomeMapping",
        entity_id=mapping_id,
        **get_request_context(request),
    )


@router.post(
    "/question-bloom-mappings",
    response_model=QuestionBloomMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_question_bloom_mapping(
    payload: QuestionBloomMappingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> QuestionBloomMapping:
    _get_or_404(db, Question, payload.question_id, "Question")
    mapping = QuestionBloomMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="question_bloom_mapping.created",
        entity_type="QuestionBloomMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get("/question-bloom-mappings", response_model=list[QuestionBloomMappingRead])
def list_question_bloom_mappings(
    question_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[QuestionBloomMapping]:
    query = db.query(QuestionBloomMapping)
    if question_id is not None:
        query = query.filter(QuestionBloomMapping.question_id == question_id)
    return query.all()


@router.delete("/question-bloom-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question_bloom_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> None:
    mapping = _get_or_404(db, QuestionBloomMapping, mapping_id, "Question-Bloom mapping")
    db.delete(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="question_bloom_mapping.deleted",
        entity_type="QuestionBloomMapping",
        entity_id=mapping_id,
        **get_request_context(request),
    )


# Assessments/assessment_questions (the graded instances) live in the
# per-program schema (docs/adr/0003-schema-per-program.md) — every route in
# this section and the next needs the `X-Program-Code` header, resolved and
# authorized by get_program_scoped_db (see app.services.rbac.get_program_context)
# before a session bound to that program's schema is ever opened. Assessment
# types/rubrics/questions above stay institution-shared (get_db).
# --- Assessments ---
@router.post("/assessments", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: AssessmentCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> Assessment:
    ensure_assigned_to_section(db, current_user.id, payload.course_section_id)
    assessment = Assessment(**payload.model_dump(), status=WorkflowStatus.DRAFT)
    db.add(assessment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment.created",
        entity_type="Assessment",
        entity_id=assessment.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return assessment


@router.get("/assessments", response_model=list[AssessmentRead])
def list_assessments(
    request: Request,
    course_section_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.view", scope_type="program")),
) -> list[Assessment]:
    if course_section_id is not None:
        ensure_section_access(db, current_user.id, course_section_id, request.state.program_id)
        return (
            db.query(Assessment)
            .filter(Assessment.course_section_id == course_section_id)
            .order_by(Assessment.created_at.desc())
            .all()
        )
    my_section_ids = filter_to_my_sections(db, current_user.id, request.state.program_id)
    query = db.query(Assessment)
    if my_section_ids is not None:
        query = query.filter(Assessment.course_section_id.in_(my_section_ids))
    return query.order_by(Assessment.created_at.desc()).all()


@router.get("/assessments/weight-summary", response_model=AssessmentWeightSummary)
def get_assessment_weight_summary(
    request: Request,
    course_section_id: uuid.UUID = Query(...),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.view", scope_type="program")),
) -> AssessmentWeightSummary:
    """Surfaced to the UI as a non-blocking banner, not enforced at
    create/update time: assessments for a section are typically added one at
    a time, so a hard "must sum to 100%" check on every write would make it
    impossible to build up to 100% incrementally."""
    ensure_section_access(db, current_user.id, course_section_id, request.state.program_id)
    assessments = (
        db.query(Assessment).filter(Assessment.course_section_id == course_section_id).all()
    )
    weighted = [a for a in assessments if a.weight is not None]
    total_weight = sum((a.weight for a in weighted), Decimal(0))
    return AssessmentWeightSummary(
        course_section_id=course_section_id,
        assessment_count=len(assessments),
        weighted_count=len(weighted),
        total_weight=total_weight,
        is_complete=len(weighted) == len(assessments) and total_weight == Decimal(100),
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentRead)
def get_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.view", scope_type="program")),
) -> Assessment:
    assessment = _get_or_404(db, Assessment, assessment_id, "Assessment")
    ensure_section_access(
        db, current_user.id, assessment.course_section_id, request.state.program_id
    )
    return assessment


@router.patch("/assessments/{assessment_id}", response_model=AssessmentRead)
def update_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> Assessment:
    assessment = _get_or_404(db, Assessment, assessment_id, "Assessment")
    ensure_assigned_to_section(db, current_user.id, assessment.course_section_id)
    previous_value = {
        "title": assessment.title,
        "max_marks": str(assessment.max_marks),
        "weight": str(assessment.weight) if assessment.weight is not None else None,
    }
    for field, value in payload.model_dump().items():
        setattr(assessment, field, value)
    db.add(assessment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment.updated",
        entity_type="Assessment",
        entity_id=assessment.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return assessment


@router.delete("/assessments/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> None:
    assessment = _get_or_404(db, Assessment, assessment_id, "Assessment")
    ensure_assigned_to_section(db, current_user.id, assessment.course_section_id)
    db.delete(assessment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment.deleted",
        entity_type="Assessment",
        entity_id=assessment_id,
        **get_request_context(request),
    )


def _validate_assessment_finalizable(db: Session, assessment: Assessment) -> None:
    """Guards the draft→submitted transition only (Faculty Module spec
    §15.1/§18/§19 all describe a one-time "finalize" check, not a re-check on
    every later stage). Which check applies is read off `AssessmentType`'s
    existing type-level flags — `requires_documents` already identifies
    exam-type assessments (seeded true only for Midterm/Final Exam), so it
    doubles as the BR-07 mark-sum discriminator without a new flag."""
    assessment_type = _get_or_404(
        db, AssessmentType, assessment.assessment_type_id, "Assessment type"
    )
    questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.assessment_id == assessment.id)
        .all()
    )

    if assessment_type.requires_documents:  # exam-type: Midterm/Final — BR-07
        total = sum((q.marks_allocated for q in questions), Decimal(0))
        if total != assessment.max_marks:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Incomplete: question marks total {total}, must total "
                f"{assessment.max_marks}.",
            )
        return

    if assessment_type.requires_cep_documents:  # Complex Engineering Problem — §18
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Add at least one task before finalizing.",
            )
        for q in questions:
            has_co = (
                db.query(QuestionCourseOutcomeMapping)
                .filter(QuestionCourseOutcomeMapping.question_id == q.question_id)
                .first()
                is not None
            )
            has_po = (
                db.query(AssessmentQuestionProgramOutcomeMapping)
                .filter(AssessmentQuestionProgramOutcomeMapping.assessment_question_id == q.id)
                .first()
                is not None
            )
            if not (has_co and has_po):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Every task must have a Course Outcome and Program Outcome "
                    "mapping before finalizing.",
                )
        return

    if assessment_type.requires_oep_validation:  # Open-Ended Problem — §19
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Add at least one task before finalizing.",
            )
        for q in questions:
            has_co = (
                db.query(QuestionCourseOutcomeMapping)
                .filter(QuestionCourseOutcomeMapping.question_id == q.question_id)
                .first()
                is not None
            )
            if not has_co:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Every task must have a Course Outcome mapping before finalizing.",
                )


@router.post("/assessments/{assessment_id}/advance", response_model=AssessmentRead)
def advance_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.approve", scope_type="program")),
) -> Assessment:
    assessment = _get_or_404(db, Assessment, assessment_id, "Assessment")
    ensure_section_access(
        db, current_user.id, assessment.course_section_id, request.state.program_id
    )
    current_status = WorkflowStatus(assessment.status)
    next_status = _NEXT_STATUS.get(current_status)
    if next_status is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assessment in status {current_status.value!r} cannot be advanced further.",
        )
    if current_status == WorkflowStatus.DRAFT:
        _validate_assessment_finalizable(db, assessment)
    previous_value = {"status": current_status.value}
    assessment.status = next_status
    db.add(assessment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment.status_changed",
        entity_type="Assessment",
        entity_id=assessment.id,
        previous_value=previous_value,
        new_value={"status": next_status.value},
        **get_request_context(request),
    )
    return assessment


# --- Assessment questions ---
@router.post(
    "/assessment-questions",
    response_model=AssessmentQuestionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment_question(
    payload: AssessmentQuestionCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> AssessmentQuestion:
    assessment = _get_or_404(db, Assessment, payload.assessment_id, "Assessment")
    ensure_assigned_to_section(db, current_user.id, assessment.course_section_id)
    _get_or_404(db, Question, payload.question_id, "Question")
    assessment_question = AssessmentQuestion(**payload.model_dump())
    db.add(assessment_question)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment_question.created",
        entity_type="AssessmentQuestion",
        entity_id=assessment_question.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return assessment_question


@router.get("/assessment-questions", response_model=list[AssessmentQuestionRead])
def list_assessment_questions(
    assessment_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("assessment.view", scope_type="program")),
) -> list[AssessmentQuestion]:
    query = db.query(AssessmentQuestion)
    if assessment_id is not None:
        query = query.filter(AssessmentQuestion.assessment_id == assessment_id)
    return query.order_by(AssessmentQuestion.sequence).all()


@router.patch(
    "/assessment-questions/{assessment_question_id}", response_model=AssessmentQuestionRead
)
def update_assessment_question(
    assessment_question_id: uuid.UUID,
    payload: AssessmentQuestionCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> AssessmentQuestion:
    assessment_question = _get_or_404(
        db, AssessmentQuestion, assessment_question_id, "Assessment question"
    )
    previous_value = {
        "marks_allocated": str(assessment_question.marks_allocated),
        "sequence": assessment_question.sequence,
    }
    for field, value in payload.model_dump().items():
        setattr(assessment_question, field, value)
    db.add(assessment_question)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment_question.updated",
        entity_type="AssessmentQuestion",
        entity_id=assessment_question.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return assessment_question


@router.delete(
    "/assessment-questions/{assessment_question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assessment_question(
    assessment_question_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> None:
    assessment_question = _get_or_404(
        db, AssessmentQuestion, assessment_question_id, "Assessment question"
    )
    db.delete(assessment_question)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment_question.deleted",
        entity_type="AssessmentQuestion",
        entity_id=assessment_question_id,
        **get_request_context(request),
    )


# --- Assessment-question PO mapping (Complex Engineering Problem tasks, §18) ---
@router.post(
    "/assessment-question-po-mappings",
    response_model=AssessmentQuestionProgramOutcomeMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment_question_po_mapping(
    payload: AssessmentQuestionProgramOutcomeMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> AssessmentQuestionProgramOutcomeMapping:
    _get_or_404(db, AssessmentQuestion, payload.assessment_question_id, "Assessment question")
    mapping = AssessmentQuestionProgramOutcomeMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment_question_po_mapping.created",
        entity_type="AssessmentQuestionProgramOutcomeMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get(
    "/assessment-question-po-mappings",
    response_model=list[AssessmentQuestionProgramOutcomeMappingRead],
)
def list_assessment_question_po_mappings(
    assessment_question_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("assessment.view", scope_type="program")),
) -> list[AssessmentQuestionProgramOutcomeMapping]:
    query = db.query(AssessmentQuestionProgramOutcomeMapping)
    if assessment_question_id is not None:
        query = query.filter(
            AssessmentQuestionProgramOutcomeMapping.assessment_question_id
            == assessment_question_id
        )
    return query.all()


@router.delete(
    "/assessment-question-po-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_assessment_question_po_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> None:
    mapping = _get_or_404(
        db, AssessmentQuestionProgramOutcomeMapping, mapping_id, "Assessment-question PO mapping"
    )
    db.delete(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment_question_po_mapping.deleted",
        entity_type="AssessmentQuestionProgramOutcomeMapping",
        entity_id=mapping_id,
        **get_request_context(request),
    )


# --- Assessment documents (question paper / moderation form / compliance
# form) — only meaningful for assessments whose AssessmentType.requires_
# documents is true, but upload/list/review don't hard-enforce that (a UI
# concern, not a data-integrity one); "pending" is intentionally NOT
# WorkflowStatus — see AssessmentDocument's docstring. ---
@router.get("/documents/pending", response_model=list[PendingAssessmentDocument])
def list_pending_assessment_documents(
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("assessment.approve", scope_type="program")),
) -> list[PendingAssessmentDocument]:
    """Everything a Course Coordinator / Program Administrator needs to
    review, across this program (the active program is already resolved by
    get_program_scoped_db from the X-Program-Code header — no cross-program
    scope_id filtering needed, unlike raw_data.py's pending-changes list,
    since a program-scoped session only ever sees one program's rows)."""
    rows = (
        db.query(AssessmentDocument, Assessment)
        .join(Assessment, AssessmentDocument.assessment_id == Assessment.id)
        .filter(AssessmentDocument.status == "pending")
        .order_by(AssessmentDocument.uploaded_at)
        .all()
    )
    return [
        PendingAssessmentDocument(
            document=AssessmentDocumentRead.model_validate(doc),
            assessment_id=assessment.id,
            assessment_title=assessment.title,
            course_section_id=assessment.course_section_id,
        )
        for doc, assessment in rows
    ]


@router.get("/assessments/{assessment_id}/documents", response_model=list[AssessmentDocumentRead])
def list_assessment_documents(
    assessment_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("assessment.view", scope_type="program")),
) -> list[AssessmentDocument]:
    _get_or_404(db, Assessment, assessment_id, "Assessment")
    return (
        db.query(AssessmentDocument)
        .filter(AssessmentDocument.assessment_id == assessment_id)
        .order_by(AssessmentDocument.document_type)
        .all()
    )


@router.post(
    "/assessments/{assessment_id}/documents",
    response_model=AssessmentDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_assessment_document(
    assessment_id: uuid.UUID,
    request: Request,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> AssessmentDocument:
    if document_type not in _DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"document_type must be one of {sorted(_DOCUMENT_TYPES)}",
        )
    _get_or_404(db, Assessment, assessment_id, "Assessment")

    key, size = save_upload(file, key_prefix=f"assessments/{assessment_id}/{document_type}")

    existing = None
    if document_type in _SINGLETON_DOCUMENT_TYPES:
        existing = (
            db.query(AssessmentDocument)
            .filter(
                AssessmentDocument.assessment_id == assessment_id,
                AssessmentDocument.document_type == document_type,
            )
            .one_or_none()
        )
    now = datetime.now(UTC)
    if existing is not None:
        # Re-upload replaces the slot in place and resets it to pending —
        # see AssessmentDocument's docstring for why there's no version history.
        old_key = existing.file_key
        existing.file_key = key
        existing.file_name = file.filename or "document"
        existing.file_size = size
        existing.content_type = file.content_type or "application/octet-stream"
        existing.status = "pending"
        existing.uploaded_by = current_user.id
        existing.uploaded_at = now
        existing.reviewed_by = None
        existing.reviewed_at = None
        existing.review_note = None
        db.add(existing)
        db.flush()
        delete_upload(old_key)
        document = existing
        action = "assessment_document.replaced"
    else:
        # Repeatable slots (_MULTI_DOCUMENT_TYPES) always land here too —
        # there's simply never an `existing` row to find for them.
        document = AssessmentDocument(
            assessment_id=assessment_id,
            document_type=document_type,
            file_key=key,
            file_name=file.filename or "document",
            file_size=size,
            content_type=file.content_type or "application/octet-stream",
            status="pending",
            uploaded_by=current_user.id,
            uploaded_at=now,
        )
        db.add(document)
        db.flush()
        action = "assessment_document.uploaded"

    write_audit_log(
        db,
        user_id=current_user.id,
        action=action,
        entity_type="AssessmentDocument",
        entity_id=document.id,
        new_value={"document_type": document_type, "file_name": document.file_name},
        **get_request_context(request),
    )
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment_document(
    document_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.create", scope_type="program")),
) -> None:
    """Only for repeatable slots (marked_rubric_sample, project_report) —
    singleton slots are replaced via re-upload, never deleted outright, so
    an assessment can't be left with zero rows for a required singleton type
    through this endpoint."""
    document = _get_or_404(db, AssessmentDocument, document_id, "Document")
    if document.document_type not in _MULTI_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This document type is replaced by re-uploading, not deleted. "
            "Upload a new file for this slot instead.",
        )
    delete_upload(document.file_key)
    db.delete(document)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment_document.deleted",
        entity_type="AssessmentDocument",
        entity_id=document_id,
        **get_request_context(request),
    )


@router.get("/documents/{document_id}/download")
def download_assessment_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("assessment.view", scope_type="program")),
) -> Response:
    document = _get_or_404(db, AssessmentDocument, document_id, "Document")
    contents = read_upload(document.file_key)
    return Response(
        content=contents,
        media_type=document.content_type,
        headers={"Content-Disposition": f'attachment; filename="{document.file_name}"'},
    )


@router.post("/documents/{document_id}/review", response_model=AssessmentDocumentRead)
def review_assessment_document(
    document_id: uuid.UUID,
    payload: AssessmentDocumentReview,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.approve", scope_type="program")),
) -> AssessmentDocument:
    document = _get_or_404(db, AssessmentDocument, document_id, "Document")
    if document.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document is already {document.status!r}.",
        )
    document.status = payload.status
    document.reviewed_by = current_user.id
    document.reviewed_at = datetime.now(UTC)
    document.review_note = payload.review_note
    db.add(document)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action=f"assessment_document.{payload.status}",
        entity_type="AssessmentDocument",
        entity_id=document.id,
        new_value={"status": payload.status, "review_note": payload.review_note},
        **get_request_context(request),
    )
    return document


@router.post(
    "/assessments/{assessment_id}/extend-document-deadline", response_model=AssessmentRead
)
def extend_document_deadline(
    assessment_id: uuid.UUID,
    payload: AssessmentDocumentDeadlineExtend,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.approve", scope_type="program")),
) -> Assessment:
    """The default document-upload deadline is the assessment's academic
    term end_date (computed client-side, not stored) — a Program
    Administrator (assessment.approve) can push it later here."""
    assessment = _get_or_404(db, Assessment, assessment_id, "Assessment")
    previous_value = {
        "document_deadline_extended_to": (
            assessment.document_deadline_extended_to.isoformat()
            if assessment.document_deadline_extended_to
            else None
        )
    }
    assessment.document_deadline_extended_to = payload.new_deadline
    assessment.document_deadline_extended_by = current_user.id
    assessment.document_deadline_extended_at = datetime.now(UTC)
    db.add(assessment)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="assessment.document_deadline_extended",
        entity_type="Assessment",
        entity_id=assessment.id,
        previous_value=previous_value,
        new_value={"document_deadline_extended_to": payload.new_deadline.isoformat()},
        **get_request_context(request),
    )
    return assessment
