"""public.role_templates — platform-editable default "user type" catalogue.

The "current user types...keep as default types so next institute can fetch
and use them" ask: instead of `DEFAULT_ROLES` living only as a hardcoded
Python list (app/seed/default_roles.py), it's now also mirrored into this
public-schema table, which a platform admin can edit (add/update/deactivate)
and `provision_tenant` reads from at seeding time (falling back to the
Python constant if this table is empty — see tenancy.py).

Data-seeds this table with the 13 roles `DEFAULT_ROLES` held as of this
migration (2026-09-12), verbatim, so rollout doesn't change behavior for a
single tenant — a literal snapshot, not an import of the Python module
(migrations are a frozen historical record; app/seed/default_roles.py can
keep evolving independently after this).

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-12 00:00:00

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (name, description, permission_codes, all_permissions, is_active) — a
# verbatim snapshot of app.seed.default_roles.DEFAULT_ROLES as of this
# migration. Kept inline (not imported) so this migration stays a frozen
# historical record.
_ROLE_TEMPLATES: list[tuple[str, str, list[str], bool, bool]] = [
    (
        "Legacy Tenant Administrator",
        "Full control within the institution's tenant (distinct from the "
        "cross-institution Super Administrator, public.platform_admins in "
        "the public schema). Includes raw_data.manage_all via the ALL "
        "sentinel: the raw-data console can reach every institution's every "
        "table. Disabled for new assignment — the role hierarchy now starts "
        "at Institution Administrator, itself created by the single global "
        "platform Super Administrator at institution provisioning time; "
        "existing holders keep their grant unchanged.",
        [],
        True,
        False,
    ),
    (
        "Institution Administrator",
        "Manages organizational structure, programs, curriculum, course "
        "delivery, and users for the institution — created by the platform "
        "Super Administrator at provisioning time, and the top of the "
        "tenant's own role hierarchy. Raw-data console access is scoped to "
        "this institution only.",
        [
            "institution.view", "org.manage", "org.view", "program.manage", "program.view",
            "program.approve", "academic_calendar.manage", "academic_calendar.view",
            "user.manage", "user.view", "role.manage", "role.view", "audit.view",
            "curriculum.view", "outcome.create", "outcome.approve", "mapping.create",
            "program_outcome_framework.manage", "section.manage", "section.view",
            "student.manage", "student.view", "grading.manage", "grading.view",
            "assessment.create", "assessment.approve", "assessment.view", "marks.enter",
            "report.generate", "raw_data.manage_institution",
        ],
        False,
        True,
    ),
    (
        "Accreditation Administrator",
        "Owns accreditation submissions and evidence across the institution.",
        [
            "org.view", "program.view", "curriculum.view", "accreditation.manage",
            "evidence.upload", "report.generate", "audit.view",
        ],
        False,
        False,
    ),
    (
        "Dean",
        "School-level oversight of curriculum and program approvals "
        "(typically scoped to one school).",
        [
            "org.view", "program.view", "program.approve", "curriculum.view",
            "outcome.approve", "user.view", "report.generate",
        ],
        False,
        False,
    ),
    (
        "Head of Department",
        "Department-level curriculum and assessment oversight "
        "(typically scoped to one department).",
        [
            "org.view", "program.view", "curriculum.view", "outcome.create",
            "mapping.create", "section.manage", "section.view", "student.view",
            "grading.view", "assessment.approve", "user.view",
        ],
        False,
        False,
    ),
    (
        "Program Administrator",
        "Full administrative control over one program's data (typically "
        "scoped to one program via UserRole.scope_type='program') — the "
        "raw-data-console peer of Institution Administrator, but scoped to "
        "a single program instead of the whole institution. Approves "
        "Program Coordinators' pending course-level raw-data changes.",
        [
            "program.view", "curriculum.view", "outcome.create", "outcome.approve",
            "mapping.create", "section.manage", "section.view", "student.manage",
            "student.view", "grading.manage", "grading.view", "assessment.create",
            "assessment.approve", "assessment.view", "marks.enter", "report.generate",
            "raw_data.manage_scoped", "raw_data.approve", "course_file.configure",
            "course_file.review", "course_file.view", "course_change_request.review",
            "program_role.manage", "term_commit.manage", "program_outcome_framework.manage",
        ],
        False,
        True,
    ),
    (
        "Program Coordinator",
        "Manages semester-level course offerings for one program (spec §6: "
        "define course offerings, create sections, assign faculty, "
        "designate course coordinator) and its curriculum/outcome "
        "definitions (typically scoped to one program). Cannot change "
        "program-level data (PEOs, POs, PO-PEO mappings) — that's Program "
        "Administrator territory. Raw-data-console writes to course-level "
        "tables are proposals, not immediate changes: a Program "
        "Administrator must approve one before it takes effect or becomes "
        "visible to others.",
        [
            "program.view", "curriculum.view", "outcome.create", "mapping.create",
            "section.manage", "section.view", "student.view", "grading.view",
            "assessment.create", "report.generate", "raw_data.propose_scoped",
            "course_file.configure", "course_file.review", "course_file.view",
            "course_change_request.review", "course_change_request.review_program",
            "course_type.manage", "program_role.manage", "curriculum_feedback.create",
        ],
        False,
        True,
    ),
    (
        "Faculty",
        "Delivers courses: creates assessments and enters marks for sections they teach.",
        [
            "curriculum.view", "mapping.create", "section.view", "student.view",
            "student.manage", "grading.view", "assessment.create", "assessment.view",
            "marks.enter", "course_file.upload", "course_file.view",
            "course_change_request.create",
        ],
        False,
        True,
    ),
    (
        "Section Coordinator",
        "Full administrative control over one course's data (typically scoped to "
        "one course via UserRole.scope_type='course') — the raw-data-console peer "
        "of Program Administrator, but scoped to a single course. Also owns that "
        "course's assessment plan and approves marks entry for its sections. "
        "Formerly two separate roles ('Course Administrator' and 'Section "
        "Coordinator'); merged because their responsibilities overlapped in "
        "practice. Unlike the original Section Coordinator, granting this role no "
        "longer requires the holder to already have a FacultyAssignment on a "
        "section of that course — it carries section.manage, the same "
        "program/institution-wide section authority Course Administrator held "
        "(see app.services.faculty_scope.is_section_authority).",
        [
            "curriculum.view", "outcome.create", "outcome.approve", "mapping.create",
            "section.manage", "section.view", "student.view", "student.manage",
            "grading.view", "assessment.create", "assessment.approve", "assessment.view",
            "marks.enter", "raw_data.manage_scoped", "course_file.configure",
            "course_file.upload", "course_file.review", "course_file.view",
            "course_change_request.create", "course_change_request.review",
            "course_change_request.review_admin", "course_type.manage",
        ],
        False,
        True,
    ),
    (
        "Examination/Assessment Administrator",
        "Institution-wide assessment scheduling and approval.",
        [
            "section.view", "grading.view", "assessment.create", "assessment.approve",
            "assessment.view", "marks.enter", "report.generate",
        ],
        False,
        False,
    ),
    (
        "Quality Assurance Officer",
        "Monitors attainment results and survey cycles for institutional QA.",
        [
            "curriculum.view", "attainment.calculate", "attainment.approve",
            "survey.manage", "report.generate", "audit.view",
        ],
        False,
        False,
    ),
    (
        "Accreditation Reviewer",
        "Reviews submitted evidence against accreditation criteria (typically external/part-time).",
        ["curriculum.view", "evidence.upload", "report.generate"],
        False,
        False,
    ),
    (
        "Student",
        "Views their own program curriculum and (from Phase 7) responds to surveys.",
        ["curriculum.view"],
        False,
        True,
    ),
    (
        "External Stakeholder",
        "Employers/alumni/advisory-board members — survey participation only (Phase 7+); "
        "no Phase 1 permissions.",
        [],
        False,
        False,
    ),
]


def upgrade() -> None:
    op.create_table(
        "role_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("permission_codes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "all_permissions", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_role_templates_name"),
        schema="public",
    )

    table = sa.table(
        "role_templates",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("permission_codes", postgresql.JSONB),
        sa.column("all_permissions", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        schema="public",
    )
    op.bulk_insert(
        table,
        [
            {
                "id": uuid.uuid4(),
                "name": name,
                "description": description,
                "permission_codes": codes,
                "all_permissions": all_perms,
                "is_active": is_active,
            }
            for name, description, codes, all_perms, is_active in _ROLE_TEMPLATES
        ],
    )


def downgrade() -> None:
    op.drop_table("role_templates", schema="public")
