"""Assessment definition (DATABASE_PLAN.md §F — implemented).

Scope: assessment types, rubrics, questions, and assessments themselves.
Marks entry/gradebook (`student_performance`, §G) is a separate later feature.
"""

from app.models.tenant.assessments.assessment import (
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
from app.models.tenant.assessments.marks import (
    AttainmentSnapshot,
    CourseAttainmentConfig,
    GradeSubmission,
    ProgramAttainmentConfig,
    StudentMark,
)

__all__ = [
    "Assessment",
    "AssessmentDocument",
    "AssessmentQuestion",
    "AssessmentQuestionProgramOutcomeMapping",
    "AssessmentType",
    "AttainmentSnapshot",
    "CourseAttainmentConfig",
    "GradeSubmission",
    "ProgramAttainmentConfig",
    "Question",
    "QuestionBloomMapping",
    "QuestionCourseOutcomeMapping",
    "Rubric",
    "RubricCriterion",
    "RubricLevel",
    "StudentMark",
]
