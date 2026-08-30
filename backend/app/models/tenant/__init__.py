"""Models living in each institution's `tenant_<slug>` schema.

Importing this package registers every implemented model (Phase 1 org/RBAC/
audit, plus the Phase 2/3 course catalog, OBE outcome hierarchy, mappings,
and accreditation framework catalogue, plus course delivery/grading and
assessment definition) on `TenantBase`'s metadata, which is what
`alembic/tenant/env.py` autogenerates against and what
`app.services.tenancy.provision_tenant` creates tables from.
"""

from app.models.tenant.accreditation import (
    AccreditationBody,
    AccreditationFramework,
    EngineeringActivity,
    FrameworkPO,
    KnowledgeProfile,
    ProblemAttribute,
)
from app.models.tenant.assessments import (
    Assessment,
    AssessmentDocument,
    AssessmentQuestion,
    AssessmentQuestionProgramOutcomeMapping,
    AssessmentType,
    AttainmentSnapshot,
    CourseAttainmentConfig,
    GradeSubmission,
    ProgramAttainmentConfig,
    Question,
    QuestionBloomMapping,
    QuestionCourseOutcomeMapping,
    Rubric,
    RubricCriterion,
    RubricLevel,
    StudentMark,
)
from app.models.tenant.audit import AuditLog, Notification
from app.models.tenant.change_requests import CourseChangeRequest
from app.models.tenant.course_files import (
    CourseFileRequirement,
    CourseFileSubmission,
    CourseFileType,
)
from app.models.tenant.courses import (
    Course,
    CourseOffering,
    CourseSection,
    CourseVersion,
    FacultyAssignment,
    GradingBand,
    GradingPolicy,
    StudentEnrollment,
)
from app.models.tenant.identity import (
    FacultyProfile,
    Permission,
    Role,
    RolePermission,
    StudentProfile,
    User,
    UserRole,
)
from app.models.tenant.mappings import (
    CourseOutcomePOMapping,
    MappingScale,
    MappingScaleLevel,
    ProgramOutcomePEOMapping,
)
from app.models.tenant.obe import PEO, BloomLevel, CourseOutcome, ImprovementPlan, ProgramOutcome
from app.models.tenant.org import (
    AcademicTerm,
    AcademicYear,
    Campus,
    Department,
    Program,
    ProgramVersion,
    School,
)
from app.models.tenant.raw_data import RawDataChangeRequest

__all__ = [
    "PEO",
    "AcademicTerm",
    "AcademicYear",
    "AccreditationBody",
    "AccreditationFramework",
    "Assessment",
    "AssessmentDocument",
    "AssessmentQuestion",
    "AssessmentQuestionProgramOutcomeMapping",
    "AssessmentType",
    "AttainmentSnapshot",
    "AuditLog",
    "BloomLevel",
    "Campus",
    "Course",
    "CourseAttainmentConfig",
    "CourseChangeRequest",
    "CourseFileRequirement",
    "CourseFileSubmission",
    "CourseFileType",
    "CourseOffering",
    "CourseOutcome",
    "CourseOutcomePOMapping",
    "CourseSection",
    "CourseVersion",
    "Department",
    "EngineeringActivity",
    "FacultyAssignment",
    "FacultyProfile",
    "FrameworkPO",
    "GradeSubmission",
    "GradingBand",
    "GradingPolicy",
    "ImprovementPlan",
    "KnowledgeProfile",
    "MappingScale",
    "MappingScaleLevel",
    "Notification",
    "Permission",
    "ProblemAttribute",
    "Program",
    "ProgramAttainmentConfig",
    "ProgramOutcome",
    "ProgramOutcomePEOMapping",
    "ProgramVersion",
    "Question",
    "QuestionBloomMapping",
    "QuestionCourseOutcomeMapping",
    "RawDataChangeRequest",
    "Role",
    "RolePermission",
    "Rubric",
    "RubricCriterion",
    "RubricLevel",
    "School",
    "StudentEnrollment",
    "StudentMark",
    "StudentProfile",
    "User",
    "UserRole",
]
