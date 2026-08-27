"""Raw-data console: generic table introspection + scoped CRUD.

Explicit, informed decision by the system owner: this gives direct read/
write/delete/update/insert access to database tables from the UI, bypassing
the workflow-gate/validation logic every other endpoint in this app goes
through. The one gate that *is* required (Program Coordinator's course-level
writes need Program Administrator approval) is implemented via
`RawDataChangeRequest`; nothing else is gated. Every write (immediate or
approved) is audit-logged by the caller (see app/api/v1/endpoints/raw_data.py)
— that's a record, not a restriction, so it doesn't reintroduce a gate.

## Table groups

Derived by hand, not from the FK graph — the FK graph doesn't encode "which
tables are program-level vs course-level" on its own, and guessing wrong
here is a real security question, not a style choice.
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass
from typing import Literal

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db.base import TenantBase

PROGRAM_LEVEL_TABLES: frozenset[str] = frozenset(
    {
        "programs",
        "program_versions",
        "peos",
        "program_outcomes",
        "program_outcome_peo_mappings",
    }
)

COURSE_LEVEL_TABLES: frozenset[str] = frozenset(
    {
        "courses",
        "course_versions",
        "course_outcomes",
        "course_outcome_po_mappings",
        "course_offerings",
        "course_sections",
        "faculty_assignments",
        "student_enrollments",
        "questions",
        "question_co_mappings",
        "question_bloom_mappings",
        "assessments",
        "assessment_questions",
        "rubrics",
        "rubric_criteria",
        "rubric_levels",
        "grading_policies",
        "grading_bands",
    }
)

# Everything else in the tenant schema — Institution Administrator and
# Super Administrator only, never Program/Course Administrator or Program
# Coordinator regardless of their scope.
_PUBLIC_TABLE_NAMES: frozenset[str] = frozenset({"institutions", "platform_admins"})


def _all_tenant_table_names() -> frozenset[str]:
    return frozenset(
        name for name, table in TenantBase.metadata.tables.items() if table.schema is None
    )


def institution_only_table_names() -> frozenset[str]:
    return _all_tenant_table_names() - PROGRAM_LEVEL_TABLES - COURSE_LEVEL_TABLES


def _t(table_name: str) -> sa.Table:
    """Look up an already-registered Table object by name — NOT
    `sa.table()` (a bare, unregistered TableClause). schema_translate_map
    only reliably applies to real, metadata-registered Table objects; the
    lightweight sa.table()/sa.column() constructs silently query the
    unqualified/default schema instead (same class of bug as
    0003_user_bio.py's op.add_column gotcha, discovered the hard way here
    via a live 500 against tenant_demo before this fix)."""
    return TenantBase.metadata.tables[table_name]


WriteMode = Literal["immediate", "propose", "denied"]


@dataclass(frozen=True)
class ScopedGrant:
    permission_code: str
    scope_type: str | None
    scope_id: uuid.UUID | None


def raw_data_grants(
    all_grants: list[tuple[str, str | None, uuid.UUID | None]],
) -> list[ScopedGrant]:
    """Filter a user's full permission-grant list (from
    app.services.rbac.get_user_permission_grants) down to the raw_data.*
    ones this module cares about."""
    return [
        ScopedGrant(code, scope_type, scope_id)
        for code, scope_type, scope_id in all_grants
        if code.startswith("raw_data.")
    ]


def has_cross_institution_access(grants: list[ScopedGrant]) -> bool:
    return any(g.permission_code == "raw_data.manage_all" for g in grants)


def accessible_table_names(grants: list[ScopedGrant]) -> set[str]:
    """Union, across every grant the user holds, of tables they can at
    least *see* (read) — write capability is a separate, per-table question,
    see `resolve_write_mode`."""
    tables: set[str] = set()
    for g in grants:
        if g.permission_code == "raw_data.manage_all":
            tables |= _all_tenant_table_names() | _PUBLIC_TABLE_NAMES
        elif g.permission_code == "raw_data.manage_institution":
            tables |= _all_tenant_table_names()
        elif g.permission_code == "raw_data.manage_scoped":
            if g.scope_type == "program":
                tables |= PROGRAM_LEVEL_TABLES | COURSE_LEVEL_TABLES
            elif g.scope_type == "course":
                tables |= COURSE_LEVEL_TABLES
        elif g.permission_code == "raw_data.propose_scoped":
            # Program Coordinator: read-only on program-level, read+propose
            # on course-level — both are still *readable*.
            tables |= PROGRAM_LEVEL_TABLES | COURSE_LEVEL_TABLES
    return tables


def resolve_write_mode(grants: list[ScopedGrant], table_name: str) -> WriteMode:
    """The most-permissive write mode the user's grants give them for this
    table, ignoring row-level scope (that's checked separately once a
    specific row/pk is known, via `build_scope_filter`)."""
    best: WriteMode = "denied"
    for g in grants:
        if g.permission_code == "raw_data.manage_all":
            return "immediate"
        if g.permission_code == "raw_data.manage_institution":
            best = "immediate"
        elif g.permission_code == "raw_data.manage_scoped":
            if g.scope_type == "program" and (
                table_name in PROGRAM_LEVEL_TABLES or table_name in COURSE_LEVEL_TABLES
            ) or g.scope_type == "course" and table_name in COURSE_LEVEL_TABLES:
                best = "immediate"
        elif (
            g.permission_code == "raw_data.propose_scoped"
            and table_name in COURSE_LEVEL_TABLES
            and best == "denied"
        ):
            best = "propose"
    return best


def _scope_ids(grants: list[ScopedGrant], scope_type: str, codes: set[str]) -> set[uuid.UUID]:
    return {
        g.scope_id
        for g in grants
        if g.scope_type == scope_type and g.permission_code in codes and g.scope_id is not None
    }


_SCOPED_WRITE_CODES = {"raw_data.manage_scoped", "raw_data.propose_scoped"}


def _course_version_ids_for_programs(db: Session, program_ids: set[uuid.UUID]) -> set[uuid.UUID]:
    """A course "belongs" to a program only once it's been offered under
    one of that program's versions (course_offerings.program_version_id) —
    Course itself only has department_id, not program_id, and a department
    can have more than one program, so this offering-based chain is the
    only structurally sound program<->course link this schema has. A course
    sitting in the catalog with no offering yet has no program scope at
    all — that's expected, not a bug."""
    if not program_ids:
        return set()
    program_versions = _t("program_versions")
    course_offerings = _t("course_offerings")
    join_cond = program_versions.c.id == course_offerings.c.program_version_id
    stmt = (
        sa.select(course_offerings.c.course_version_id)
        .select_from(course_offerings.join(program_versions, join_cond))
        .where(program_versions.c.program_id.in_(program_ids))
        .distinct()
    )
    return {row[0] for row in db.execute(stmt)}


def _course_offering_ids_for_programs(db: Session, program_ids: set[uuid.UUID]) -> set[uuid.UUID]:
    if not program_ids:
        return set()
    program_versions = _t("program_versions")
    course_offerings = _t("course_offerings")
    join_cond = program_versions.c.id == course_offerings.c.program_version_id
    stmt = (
        sa.select(course_offerings.c.id)
        .select_from(course_offerings.join(program_versions, join_cond))
        .where(program_versions.c.program_id.in_(program_ids))
    )
    return {row[0] for row in db.execute(stmt)}


def _course_section_ids_for_offerings(db: Session, offering_ids: set[uuid.UUID]) -> set[uuid.UUID]:
    if not offering_ids:
        return set()
    course_sections = _t("course_sections")
    stmt = sa.select(course_sections.c.id).where(
        course_sections.c.course_offering_id.in_(offering_ids)
    )
    return {row[0] for row in db.execute(stmt)}


@dataclass(frozen=True)
class _ScopeIdSets:
    program_ids: set[uuid.UUID]
    course_ids: set[uuid.UUID]
    program_version_ids: set[uuid.UUID]
    course_version_ids: set[uuid.UUID]
    course_offering_ids: set[uuid.UUID]
    course_section_ids: set[uuid.UUID]


def _resolve_scope_id_sets(db: Session, grants: list[ScopedGrant]) -> _ScopeIdSets:
    program_ids = _scope_ids(grants, "program", _SCOPED_WRITE_CODES)
    course_ids = _scope_ids(grants, "course", {"raw_data.manage_scoped"})

    program_version_ids: set[uuid.UUID] = set()
    if program_ids:
        program_versions = _t("program_versions")
        stmt = sa.select(program_versions.c.id).where(
            program_versions.c.program_id.in_(program_ids)
        )
        program_version_ids = {row[0] for row in db.execute(stmt)}

    course_version_ids = _course_version_ids_for_programs(db, program_ids)
    if course_ids:
        course_versions = _t("course_versions")
        stmt = sa.select(course_versions.c.id).where(course_versions.c.course_id.in_(course_ids))
        course_version_ids |= {row[0] for row in db.execute(stmt)}

    course_offering_ids = _course_offering_ids_for_programs(db, program_ids)
    if course_version_ids:
        course_offerings = _t("course_offerings")
        stmt = sa.select(course_offerings.c.id).where(
            course_offerings.c.course_version_id.in_(course_version_ids)
        )
        course_offering_ids |= {row[0] for row in db.execute(stmt)}

    course_section_ids = _course_section_ids_for_offerings(db, course_offering_ids)

    return _ScopeIdSets(
        program_ids=program_ids,
        course_ids=course_ids,
        program_version_ids=program_version_ids,
        course_version_ids=course_version_ids,
        course_offering_ids=course_offering_ids,
        course_section_ids=course_section_ids,
    )


# table_name -> (fk_column_name, which _ScopeIdSets attribute it filters against)
_PROGRAM_LEVEL_FILTER: dict[str, tuple[str, str]] = {
    "program_versions": ("program_id", "program_ids"),
    "peos": ("program_version_id", "program_version_ids"),
    "program_outcomes": ("program_version_id", "program_version_ids"),
}
_COURSE_LEVEL_FILTER: dict[str, tuple[str, str]] = {
    # "course_versions" is deliberately absent here — it needs the union of
    # program-scope AND course-scope id sets, handled as a special case
    # below rather than through this single-column-filter table.
    "course_outcomes": ("course_version_id", "course_version_ids"),
    "course_offerings": ("id", "course_offering_ids"),
    "course_sections": ("course_offering_id", "course_offering_ids"),
    "faculty_assignments": ("course_section_id", "course_section_ids"),
    "student_enrollments": ("course_section_id", "course_section_ids"),
    "questions": ("course_version_id", "course_version_ids"),
    "assessments": ("course_section_id", "course_section_ids"),
    "grading_policies": ("program_version_id", "program_version_ids"),
}


def build_scope_filter(
    db: Session, table: sa.Table, grants: list[ScopedGrant]
) -> sa.ColumnElement | None:
    """`None` means "no filtering, every row visible" (manage_all /
    manage_institution). Otherwise an OR of every scope the user's grants
    cover for this specific table; `sa.false()` if none apply (table is in
    their allowlist but no grant actually reaches any row of it — e.g. a
    Program Administrator whose program has no course_offerings yet)."""
    if any(
        g.permission_code in ("raw_data.manage_all", "raw_data.manage_institution")
        for g in grants
    ):
        return None

    ids = _resolve_scope_id_sets(db, grants)
    table_name = table.name

    if table_name == "programs":
        return table.c.id.in_(ids.program_ids) if ids.program_ids else sa.false()
    if table_name in _PROGRAM_LEVEL_FILTER:
        col, attr = _PROGRAM_LEVEL_FILTER[table_name]
        values = getattr(ids, attr)
        return table.c[col].in_(values) if values else sa.false()
    if table_name == "program_outcome_peo_mappings":
        # program_outcome_id -> program_outcomes, already scoped above.
        program_outcomes = _t("program_outcomes")
        if not ids.program_version_ids:
            return sa.false()
        po_ids_stmt = sa.select(program_outcomes.c.id).where(
            program_outcomes.c.program_version_id.in_(ids.program_version_ids)
        )
        po_ids = {row[0] for row in db.execute(po_ids_stmt)}
        return table.c.program_outcome_id.in_(po_ids) if po_ids else sa.false()
    if table_name == "courses":
        # A course is in scope if any of its versions are in scope.
        course_versions = _t("course_versions")
        if not ids.course_version_ids:
            return sa.false()
        stmt = sa.select(course_versions.c.course_id).where(
            course_versions.c.id.in_(ids.course_version_ids)
        )
        course_ids_in_scope = {row[0] for row in db.execute(stmt)}
        return table.c.id.in_(course_ids_in_scope) if course_ids_in_scope else sa.false()
    if table_name == "course_versions":
        return table.c.id.in_(ids.course_version_ids) if ids.course_version_ids else sa.false()
    if table_name in _COURSE_LEVEL_FILTER:
        col, attr = _COURSE_LEVEL_FILTER[table_name]
        values = getattr(ids, attr)
        return table.c[col].in_(values) if values else sa.false()
    if table_name == "course_outcome_po_mappings":
        course_outcomes = _t("course_outcomes")
        if not ids.course_version_ids:
            return sa.false()
        stmt = sa.select(course_outcomes.c.id).where(
            course_outcomes.c.course_version_id.in_(ids.course_version_ids)
        )
        co_ids = {row[0] for row in db.execute(stmt)}
        return table.c.course_outcome_id.in_(co_ids) if co_ids else sa.false()
    if table_name in ("question_co_mappings", "question_bloom_mappings"):
        questions = _t("questions")
        if not ids.course_version_ids:
            return sa.false()
        stmt = sa.select(questions.c.id).where(
            questions.c.course_version_id.in_(ids.course_version_ids)
        )
        q_ids = {row[0] for row in db.execute(stmt)}
        return table.c.question_id.in_(q_ids) if q_ids else sa.false()
    if table_name == "assessment_questions":
        assessments = _t("assessments")
        if not ids.course_section_ids:
            return sa.false()
        stmt = sa.select(assessments.c.id).where(
            assessments.c.course_section_id.in_(ids.course_section_ids)
        )
        a_ids = {row[0] for row in db.execute(stmt)}
        return table.c.assessment_id.in_(a_ids) if a_ids else sa.false()
    if table_name in ("rubrics", "rubric_criteria", "rubric_levels"):
        # Rubrics are reusable/institution-wide reference data (see
        # app.models.tenant.assessments) with no program/course FK at all —
        # visible read-only to anyone who can see COURSE_LEVEL_TABLES, since
        # excluding them entirely would make the "attach a rubric" flow
        # unusable for scoped roles. No row-level scoping is possible here.
        return None
    if table_name == "grading_bands":
        grading_policies = _t("grading_policies")
        if not ids.program_version_ids:
            return sa.false()
        stmt = sa.select(grading_policies.c.id).where(
            grading_policies.c.program_version_id.in_(ids.program_version_ids)
        )
        gp_ids = {row[0] for row in db.execute(stmt)}
        return table.c.grading_policy_id.in_(gp_ids) if gp_ids else sa.false()

    # Unrecognized table reached this far only if it's in the allowlist but
    # we forgot to wire its filter — fail closed, not open.
    return sa.false()


def resolve_scope_for_write(
    db: Session, grants: list[ScopedGrant], table_name: str
) -> tuple[str, uuid.UUID] | None:
    """For a write that needs to be recorded with a specific
    (scope_type, scope_id) — either because it's going into
    RawDataChangeRequest, or just for audit-log context — pick the single
    scoped grant responsible. Prefers a 'course' scope over 'program' when
    both apply (more specific), and the first matching grant otherwise.
    Returns None for institution-wide/cross-institution grants (no single
    scope applies)."""
    course_grant = next(
        (g for g in grants if g.scope_type == "course" and g.scope_id is not None),
        None,
    )
    if course_grant is not None and table_name in COURSE_LEVEL_TABLES:
        return ("course", course_grant.scope_id)  # type: ignore[return-value]
    program_grant = next(
        (g for g in grants if g.scope_type == "program" and g.scope_id is not None),
        None,
    )
    if program_grant is not None:
        return ("program", program_grant.scope_id)  # type: ignore[return-value]
    return None


# --- Table/column metadata + generic row (de)serialization -----------------

_TYPE_TAGS: dict[type, str] = {}


def get_table(table_name: str, *, allow_public: bool = False) -> sa.Table:
    table = TenantBase.metadata.tables.get(table_name)
    if table is None:
        raise LookupError(f"Unknown table {table_name!r}")
    if table.schema == "public" and not allow_public:
        raise PermissionError(f"Table {table_name!r} requires cross-institution access")
    if table.schema not in (None, "public"):
        raise LookupError(f"Unknown table {table_name!r}")
    return table


def column_type_tag(column: sa.Column) -> str:
    python_type = None
    with contextlib.suppress(NotImplementedError):
        python_type = column.type.python_type
    type_name = type(column.type).__name__.lower()
    if "uuid" in type_name:
        return "uuid"
    if "bool" in type_name:
        return "boolean"
    if "jsonb" in type_name or "json" in type_name:
        return "json"
    if "numeric" in type_name or "decimal" in type_name:
        return "numeric"
    if "datetime" in type_name:
        return "datetime"
    if "date" in type_name:
        return "date"
    if "text" in type_name:
        return "text"
    if "integer" in type_name:
        return "integer"
    if python_type is str:
        return "string"
    return "string"


def foreign_key_ref(column: sa.Column) -> str | None:
    for fk in column.foreign_keys:
        return f"{fk.column.table.name}.{fk.column.name}"
    return None


def serialize_value(value: object) -> object:
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    # Decimal and anything else JSON can't natively handle.
    if type(value).__name__ == "Decimal":
        return str(value)
    return value


def serialize_row(row: sa.Row) -> dict[str, object]:
    return {key: serialize_value(value) for key, value in row._mapping.items()}


def coerce_input_value(column: sa.Column, value: object) -> object:
    """Cast an incoming JSON-decoded value to what the column's SQLAlchemy
    type expects, using the column's own type info rather than a hand-built
    per-table mapping."""
    if value is None:
        return None
    tag = column_type_tag(column)
    if tag == "uuid" and isinstance(value, str):
        return uuid.UUID(value)
    if tag == "numeric" and not isinstance(value, str):
        return str(value)
    return value


def primary_key_column(table: sa.Table) -> sa.Column:
    pk_cols = list(table.primary_key.columns)
    if len(pk_cols) != 1:
        raise ValueError(f"Table {table.name!r} does not have exactly one primary key column")
    return pk_cols[0]
