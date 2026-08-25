"""Models living in each institution's `tenant_<slug>` schema.

Importing this package registers every Phase 1 model on `TenantBase`'s
metadata, which is what `alembic/tenant/env.py` autogenerates against and
what `app.services.tenancy.provision_tenant` creates tables from.
"""

from app.models.tenant.audit import AuditLog, Notification
from app.models.tenant.identity import (
    FacultyProfile,
    Permission,
    Role,
    RolePermission,
    StudentProfile,
    User,
    UserRole,
)
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
    "AuditLog",
    "Notification",
    "FacultyProfile",
    "Permission",
    "Role",
    "RolePermission",
    "StudentProfile",
    "User",
    "UserRole",
    "AcademicTerm",
    "AcademicYear",
    "Campus",
    "Department",
    "Program",
    "ProgramVersion",
    "School",
]
