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
    PermissionDef(
        "program_role.manage",
        "Grant/revoke Faculty and Section Coordinator roles "
        "for people within one's own program — a narrower, program-scoped peer of "
        "role.manage, not a proxy for institution-wide user/role administration",
        "identity",
    ),
    PermissionDef(
        "term_commit.manage",
        "Enable early Final Commit for a term and permanently commit it, locking "
        "every assessment/marks/attainment write for that term in one's own program",
        "org",
    ),
    # --- Curriculum / OBE outcomes (Phase 3 — reserved) ---
    PermissionDef("curriculum.view", "View curriculum (PEOs/POs/PSOs/COs)", "curriculum"),
    PermissionDef("outcome.create", "Create outcome definitions", "curriculum"),
    PermissionDef("outcome.approve", "Approve outcome definitions", "curriculum"),
    PermissionDef("mapping.create", "Create outcome mappings", "curriculum"),
    # Program-level outcome framework (PEOs, POs, and PO<->PEO mappings) is a
    # narrower, more privileged slice of the codes above: outcome.create/
    # outcome.approve/mapping.create also gate course-level CourseOutcome and
    # CO<->PO mapping work, which Program Coordinator legitimately needs for
    # their trimester-side duties. Program Coordinator must NOT be able to
    # edit PEOs/POs directly (Master_Architecture_Part1.md §25/§43 — view +
    # feedback only there) so those specific endpoints require this separate
    # code instead, held only by Institution/Program Administrator.
    PermissionDef(
        "program_outcome_framework.manage",
        "Create/edit/publish program-level outcome framework (PEOs, POs, "
        "and PO<->PEO mappings) — distinct from course-level "
        "outcome.create/mapping.create",
        "curriculum",
    ),
    # Program Coordinator has view-only access to the program-level outcome
    # framework (spec §25) — this is their one write action at that level:
    # submitting feedback, never editing the item itself. Reviewing feedback
    # is gated on program_outcome_framework.manage instead of a separate
    # code, since it's the same tier that already owns the framework.
    PermissionDef(
        "curriculum_feedback.create",
        "Submit feedback on a read-only Program & Curriculum Level item",
        "curriculum",
    ),
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
    PermissionDef(
        "audit.manage", "Configure audit-log retention/archiving settings", "audit"
    ),
    # --- Raw data console (phpMyAdmin-style table browser/editor) ---
    PermissionDef(
        "raw_data.manage_all",
        "Raw table read/write/delete across every institution",
        "raw_data",
    ),
    PermissionDef(
        "raw_data.manage_institution",
        "Raw table read/write/delete within one's own institution",
        "raw_data",
    ),
    PermissionDef(
        "raw_data.manage_scoped",
        "Raw table read/write/delete within one's own program or course scope",
        "raw_data",
    ),
    PermissionDef(
        "raw_data.propose_scoped",
        "Raw table read + write-by-proposal (pending approval) within one's "
        "own program's course-level tables; program-level tables are read-only",
        "raw_data",
    ),
    PermissionDef(
        "raw_data.approve",
        "Approve or reject pending raw-data change proposals",
        "raw_data",
    ),
    # --- Course files (Faculty Module spec §5-9) ---
    PermissionDef(
        "course_file.configure",
        "Configure per-semester course-file requirements (required/optional, deadlines)",
        "course_files",
    ),
    PermissionDef(
        "course_file.upload", "Upload course files for an assigned section", "course_files"
    ),
    PermissionDef("course_file.review", "Approve/reject submitted course files", "course_files"),
    PermissionDef("course_file.view", "View course files and their requirements", "course_files"),
    # --- Course Settings change requests (Faculty Module spec §4.2) ---
    PermissionDef(
        "course_change_request.create",
        "Propose a change to admin-controlled course information",
        "course_change_request",
    ),
    PermissionDef(
        "course_change_request.review",
        "Approve or reject a course change request",
        "course_change_request",
    ),
    # --- Course-Level Settings and Approval Workflow ---
    PermissionDef(
        "course_type.manage",
        "Add/deactivate Course Types and configure which course-level "
        "sections are editable per type",
        "course_change_request",
    ),
    PermissionDef(
        "course_change_request.review_admin",
        "Stage-1 (Section Coordinator) review of a course change request",
        "course_change_request",
    ),
    PermissionDef(
        "course_change_request.review_program",
        "Stage-2 (Program Coordinator) final review of a two-stage course "
        "change request",
        "course_change_request",
    ),
]

PERMISSION_CODES: frozenset[str] = frozenset(p.code for p in PERMISSIONS)
