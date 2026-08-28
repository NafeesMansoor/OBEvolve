"""Assessment definition (DATABASE_PLAN.md §F — implemented).

Scope: assessment types, rubrics, questions, and assessments themselves.
Marks entry/gradebook (`student_performance`, §G) is a separate later feature.
"""

from app.models.tenant.assessments.assessment import (
    Assessment,
    AssessmentDocument,
    AssessmentQuestion,
    AssessmentType,
    Question,
    QuestionBloomMapping,
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

__all__ = [
    "Assessment",
    "AssessmentDocument",
    "AssessmentQuestion",
    "AssessmentType",
    "CourseAttainmentConfig",
    "ProgramAttainmentConfig",
    "Question",
    "QuestionBloomMapping",
    "QuestionCourseOutcomeMapping",
    "Rubric",
    "RubricCriterion",
    "RubricLevel",
    "StudentMark",
]
