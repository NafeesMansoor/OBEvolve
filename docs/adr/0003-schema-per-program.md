# ADR 0003: Schema-per-program, one level deeper than schema-per-tenant

## Status
Accepted, implemented.

## Context
[ADR 0001](0001-schema-per-tenant.md) gives each **institution** its own
PostgreSQL schema. In production use an institution can run more than one
program (e.g. ULAB runs both a B.Sc. in CSE and a B.Sc. in Software
Engineering), and the same isolation argument ADR 0001 makes for
institutions applies one level down: a program's curriculum, course
delivery, and assessment data should not depend on application-code
discipline to stay separated from another program's, and a raw-data console
row-filter is not the same guarantee as a physical schema boundary.

Two options were considered:
1. Keep everything in the tenant schema, add a `program_id` column to every
   program-specific table, and filter by it everywhere (mirrors the
   rejected option 1/2 from ADR 0001, one level down).
2. Schema-per-program: a second, nested schema per program, using the same
   `schema_translate_map` mechanism ADR 0001 already established.

## Decision
Schema-per-program (option 2) — a second marker schema, `"program"`, nested
inside each institution's schema.

## Mechanism

**Two schema tiers per institution:**
- `tenant_<slug>` (unchanged) — **institution-shared**: identity/RBAC
  (`users`, `roles`, `permissions`, `role_permissions`, `user_roles`), org
  structure (`campuses` … `programs` — the program *registry*, not
  curricula), the accreditation catalogue, shared OBE config
  (`bloom_levels`, `mapping_scales`), the **course catalog**
  (`courses`, `course_versions`, `course_outcomes`, `questions`,
  `assessment_types`, `rubrics`), grading policy, and audit/operational
  tables.
- `tenant_<slug>__<program_code>` (new, lowercased — see
  `program_schema_name()` below) — **program-specific**: `program_versions`
  (curricula), `peos`, `program_outcomes`, `program_outcome_peo_mappings`,
  `course_offerings`, `course_sections`, `faculty_assignments`,
  `student_enrollments`, `course_outcome_po_mappings`, `assessments`,
  `assessment_questions`, `student_marks`, `course_attainment_configs`*,
  `program_attainment_configs`, `improvement_plans`.

  <sub>* `course_attainment_configs` is the one exception that looks like it
  should be program-specific but isn't — see its own docstring
  (`app/models/tenant/assessments/marks.py`): it references
  `course_versions`, which stays institution-shared, and a real FK can only
  target one schema.</sub>

**Why the split lands here and not elsewhere:** `courses`/`course_versions`/
`course_outcomes` stay shared because a co-offered course (`Course.
co_offered_with_id`) needs one canonical course row selectable from
multiple programs — duplicating the catalog per program would defeat that.
What's genuinely program-specific is a program's *use* of a course: which
curriculum it's offered under, how that program maps the course's COs to
its own POs, who teaches which section, who's enrolled, what's assessed.

**In SQLAlchemy:** program-specific models get `__table_args__ =
{"schema": "program"}` — a fixed marker string, not a real schema name.
Per-request, the session binds
`execution_options(schema_translate_map={None: institution_schema, "program": institution_schema + "__" + program_code})`
— the same mechanism ADR 0001 established, just extended by one key.
A session bound this way can join an institution-shared table to a
program-schema table in one query without a special case (e.g.
`course_offerings.course_version_id → course_versions.id`).

**The one non-obvious SQLAlchemy gotcha, found the hard way:** unlike the
`None` key, SQLAlchemy does **not** infer a FK target's schema from the
*referencing* table's own `schema=`. A same-`schema="program"` FK
(`AssessmentQuestion.assessment_id → assessments.id`, both schema="program")
must still spell out `ForeignKey("program.assessments.id")` — the dotted
`"program."` prefix — or SQLAlchemy resolves the unqualified name against a
phantom `schema=None` table that never exists. Every program-schema model's
docstring repeats this because it is easy to get wrong and the failure mode
(`UndefinedTable` at query time, not at model-definition time) is confusing.

**Resolving which program a request is for:** a user can hold multiple
program-scoped role grants (e.g. Program Coordinator for two programs), so
it can't always be inferred from grants alone. An `X-Program-Code` header
(mirroring `X-Institution-Slug`) is required on any endpoint touching
program-specific tables. `app.services.rbac.get_program_context` resolves
it to a `Program` row and 403s unless the caller holds either an
institution-wide grant (any permission, unscoped) or a grant scoped to that
exact program (`scope_type="program"`, `scope_id==program.id`) — this runs
**before** any program-schema session is opened, so an unauthorized caller
never gets a query bound to a schema they have no grant for, regardless of
the specific permission the endpoint itself goes on to check. Endpoints
touching only institution-shared tables (courses, users, org structure)
don't need the header, and a few genuinely program-agnostic lookups
(`GET /org/programs`, `GET /org/academic-terms`) are deliberately open to
any authenticated user rather than gated at all — see their own docstrings.

**Physical schema naming:** `Program.code` is stored as entered (e.g.
`"BSCSE"`), but the physical schema name is lowercased
(`tenant_ulab-cse__bscse`) by `provision_program_schema()`. Every call site
that needs the physical name **must** go through the one canonical
`app.db.tenancy.program_schema_name(institution_schema, program_code)`
helper rather than building the string inline — an earlier version of this
code had several inline `f"{institution_schema}__{code}"` constructions
that silently queried a schema that never existed (`..._BSCSE` instead of
the real `..._bscse`) until consolidated into that one function.

**Migrations:** a third independent Alembic chain, `alembic/program/`,
parallel to `alembic/public/` and `alembic/tenant/`, applied once *per
program schema* the same way the tenant chain applies once per tenant
schema. `provision_program_schema(institution_schema, program_code)` —
`CREATE SCHEMA IF NOT EXISTS` + `alembic upgrade head` against it — is
called right after a `Program` row is inserted (`POST /org/programs`),
mirroring `provision_tenant()`'s schema-then-migrate sequencing.

## Trade-offs accepted
- A cross-schema FK inference gotcha (above) that cost real debugging time
  and now needs a docstring on every affected model to avoid repeating.
- One more Alembic chain to keep in sync, and one more loop
  (`scripts/migrate_all_programs.py`) alongside
  `scripts/migrate_all_tenants.py`.
- `X-Program-Code` is one more header every program-scoped frontend request
  must carry — handled centrally by `ActiveProgramProvider`
  (`frontend/src/lib/active-program-context.tsx`), not by each call site.
- **Found live, fixed same session**: react-query cache keys for
  program-scoped list queries didn't include the active program code, so
  switching the active program via the UI switcher updated the
  `X-Program-Code` header but kept serving the *previous* program's cached
  data until something unrelated happened to remount the query. Fixed by
  having `ActiveProgramProvider.setActiveProgram` invalidate the entire
  react-query cache on an actual switch (blunt, but switching programs is a
  rare, deliberate action, not a per-render cost) rather than auditing and
  fixing every individual query key.
