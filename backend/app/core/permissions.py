"""The fixed permission-code catalogue (ARCHITECTURE.md §3).

RBAC in this codebase is **permission-code based, never role-name based** —
application code calls `require_permission("curriculum.approve")`, never
`if role.name == "Dean"`. This module is the single source of truth for
every valid code; `app/seed/default_permissions.py` loads these into the
`permissions` table, and role→permission defaults live in
`app/seed/default_roles.py`.

Codes for Phase 2+ modules (assessment, attainment, survey, accreditation,
...) are listed now — per spec §5/§29 the permission catalogue is fixed up
front even though the tables/endpoints they guard land in later phases —
but nothing in Phase 1 grants or checks them.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionDef:
    code: str
    description: str
    module: str


PERMISSIONS: list[PermissionDef] = [
    # --- Institution / platform administration ---
    PermissionDef("institution.manage", "Create/update/suspend institutions", "institution"),
    PermissionDef("institution.view", "View institution details", "institution"),
    # --- Organizational structure (Phase 1) ---
    PermissionDef("org.manage", "Create/update/deactivate campuses/schools/departments", "org"),
    PermissionDef("org.view", "View organizational structure", "org"),
    PermissionDef("program.manage", "Create/update programs and program versions", "org"),
    PermissionDef("program.view", "View programs and program versions", "org"),
    PermissionDef("program.approve", "Approve/publish a program version", "org"),
    PermissionDef("academic_calendar.manage", "Manage academic years/terms", "org"),
    PermissionDef("academic_calendar.view", "View academic years/terms", "org"),
    # --- Identity & RBAC (Phase 1) ---
    PermissionDef("user.manage", "Create/update/deactivate users within a tenant", "identity"),
    PermissionDef("user.view", "View users within a tenant", "identity"),
    PermissionDef("role.manage", "Create/update roles and role-permission grants", "identity"),
    PermissionDef("role.view", "View roles and permissions", "identity"),
    # --- Curriculum / OBE outcomes (Phase 3 — reserved) ---
    PermissionDef("curriculum.view", "View curriculum (PEOs/POs/PSOs/COs)", "curriculum"),
    PermissionDef("outcome.create", "Create outcome definitions", "curriculum"),
    PermissionDef("outcome.approve", "Approve outcome definitions", "curriculum"),
    PermissionDef("mapping.create", "Create outcome mappings", "curriculum"),
    # --- Course delivery: sections, faculty assignment, students, grading ---
    PermissionDef(
        "section.manage",
        "Manage course offerings, sections, and faculty assignments",
        "delivery",
    ),
    PermissionDef(
        "section.view",
        "View course offerings, sections, and faculty assignments",
        "delivery",
    ),
    PermissionDef(
        "student.manage",
        "Create/update students, enrollments, and curriculum alignment",
        "delivery",
    ),
    PermissionDef(
        "student.view", "View students, enrollments, and curriculum alignment", "delivery"
    ),
    PermissionDef("grading.manage", "Manage grading policies", "delivery"),
    PermissionDef("grading.view", "View grading policies", "delivery"),
    # --- Assessment (Phase 5 — reserved) ---
    PermissionDef("assessment.create", "Create assessments/questions", "assessment"),
    PermissionDef("assessment.approve", "Approve assessments", "assessment"),
    PermissionDef("assessment.view", "View assessments/questions", "assessment"),
    PermissionDef("marks.enter", "Enter/record student marks", "assessment"),
    # --- Attainment engine (Phase 6 — reserved) ---
    PermissionDef("attainment.calculate", "Trigger an attainment calculation run", "attainment"),
    PermissionDef("attainment.approve", "Approve attainment results", "attainment"),
    # --- Continuous improvement / surveys (Phase 7 — reserved) ---
    PermissionDef("survey.manage", "Create/manage survey templates and instances", "survey"),
    # --- Accreditation (Phase 8 — reserved) ---
    PermissionDef("evidence.upload", "Upload accreditation evidence", "accreditation"),
    PermissionDef("accreditation.manage", "Manage accreditation submissions", "accreditation"),
    # --- Reporting (Phase 9 — reserved) ---
    PermissionDef("report.generate", "Generate reports", "reporting"),
    # --- Audit (Phase 1) ---
    PermissionDef("audit.view", "View audit logs", "audit"),
]

PERMISSION_CODES: frozenset[str] = frozenset(p.code for p in PERMISSIONS)
