"""Models living in each institution's `tenant_<slug>` schema.

Importing this package registers every implemented model (Phase 1 org/RBAC/
audit, plus the Phase 2/3 course catalog, OBE outcome hierarchy, mappings,
and accreditation framework catalogue) on `TenantBase`'s metadata, which is
what `alembic/tenant/env.py` autogenerates against and what
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
from app.models.tenant.audit import AuditLog, Notification
from app.models.tenant.courses import Course, CourseVersion
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
from app.models.tenant.obe import PEO, BloomLevel, CourseOutcome, ProgramOutcome
from app.models.tenant.org import (
    AcademicTerm,
    AcademicYear,
    Campus,
    Department,
    Program,
    ProgramVersion,
    School,
)

__all__ = [
    "PEO",
    "AcademicTerm",
    "AcademicYear",
    "AccreditationBody",
    "AccreditationFramework",
    "AuditLog",
    "BloomLevel",
    "Campus",
    "Course",
    "CourseOutcome",
    "CourseOutcomePOMapping",
    "CourseVersion",
    "Department",
    "EngineeringActivity",
    "FacultyProfile",
    "FrameworkPO",
    "KnowledgeProfile",
    "MappingScale",
    "MappingScaleLevel",
    "Notification",
    "Permission",
    "ProblemAttribute",
    "Program",
    "ProgramOutcome",
    "ProgramOutcomePEOMapping",
    "ProgramVersion",
    "Role",
    "RolePermission",
    "School",
    "StudentProfile",
    "User",
    "UserRole",
]
