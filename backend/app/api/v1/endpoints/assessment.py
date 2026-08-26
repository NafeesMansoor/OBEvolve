"""CRUD for assessment definition (DATABASE_PLAN.md §F): assessment types,
rubrics, questions, assessments. Marks entry/gradebook is a separate, later
feature — out of scope here (see `app.models.tenant.assessments` README).

Type listing is `assessment.view`; creating custom types is `assessment.create`;
question/assessment workflow-advance is `assessment.approve` — matching the
shared workflow shape used elsewhere (ARCHITECTURE.md §4).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.base import WorkflowStatus
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.assessments import (
    Assessment,
    AssessmentQuestion,
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
    AssessmentQuestionCreate,
    AssessmentQuestionRead,
    AssessmentRead,
    AssessmentTypeCreate,
    AssessmentTypeRead,
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
from app.services.audit import write_audit_log
from app.services.rbac import require_permission

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
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[Question]:
    query = db.query(Question)
    if course_version_id is not None:
        query = query.filter(Question.course_version_id == course_version_id)
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


# --- Assessments ---
@router.post("/assessments", response_model=AssessmentRead, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: AssessmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> Assessment:
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
    course_section_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> list[Assessment]:
    query = db.query(Assessment)
    if course_section_id is not None:
        query = query.filter(Assessment.course_section_id == course_section_id)
    return query.order_by(Assessment.created_at.desc()).all()


@router.get("/assessments/{assessment_id}", response_model=AssessmentRead)
def get_assessment(
    assessment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
) -> Assessment:
    return _get_or_404(db, Assessment, assessment_id, "Assessment")


@router.patch("/assessments/{assessment_id}", response_model=AssessmentRead)
def update_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> Assessment:
    assessment = _get_or_404(db, Assessment, assessment_id, "Assessment")
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> None:
    assessment = _get_or_404(db, Assessment, assessment_id, "Assessment")
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


@router.post("/assessments/{assessment_id}/advance", response_model=AssessmentRead)
def advance_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.approve")),
) -> Assessment:
    assessment = _get_or_404(db, Assessment, assessment_id, "Assessment")
    current_status = WorkflowStatus(assessment.status)
    next_status = _NEXT_STATUS.get(current_status)
    if next_status is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Assessment in status {current_status.value!r} cannot be advanced further.",
        )
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
) -> AssessmentQuestion:
    _get_or_404(db, Assessment, payload.assessment_id, "Assessment")
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
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("assessment.view")),
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assessment.create")),
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
