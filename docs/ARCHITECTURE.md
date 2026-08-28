# OBEvolve — Architecture

## 1. Overview

OBEvolve is a multi-tenant Outcome-Based Education (OBE) and accreditation
management platform. It is built as a **modular monolith** (not microservices
— see [ADR 0001](adr/0001-schema-per-tenant.md) for the tenancy decision) with
a FastAPI backend and a React/TypeScript frontend, sharing one PostgreSQL
database via a two-tier schema hierarchy: one schema per institution
([ADR 0001](adr/0001-schema-per-tenant.md)), and inside that, one schema per
program ([ADR 0003](adr/0003-schema-per-program.md)).

```
React + TS (Vite, Tailwind, shadcn/ui)
        │  REST (OpenAPI), JWT bearer
        ▼
FastAPI backend (modular monolith)
  ├─ core/         config, security, permissions
  ├─ api/v1/       versioned REST endpoints (thin controllers)
  ├─ services/     business logic (rbac, tenancy, audit, attainment engine, raw_data)
  ├─ models/       SQLAlchemy ORM (public / tenant-shared / program schema)
  ├─ seed/         default permissions/roles, BAETE v3.0 framework catalogue
  └─ middleware/   tenant resolution, audit logging
        │
        ▼
PostgreSQL: public schema + tenant_<slug> per institution
            + tenant_<slug>__<program_code> per program
```

Redis/Celery are wired (`app/workers/celery_app.py`, `docker-compose.yml`)
but nothing in the product actually uses them yet — every calculation in the
system (attainment included) runs synchronously, on demand, inside the
request that asks for it. Treat that infrastructure as reserved for a future
async job (bulk import, scheduled report generation), not as something
currently in the request path.

## 2. Multi-tenancy: schema-per-tenant, schema-per-program

- A **`public`** schema holds cross-tenant control data only: `institutions`
  (tenant registry) and `platform_admins` (the only role that spans
  institutions — see §3).
- Every institution-shared table (users, RBAC, org structure, course
  catalog, grading, accreditation catalogue, audit log) is defined **once**
  in SQLAlchemy with no hardcoded schema, and is physically created in a
  `tenant_<slug>` schema per institution.
- Every program-specific table (curricula/PEOs/POs, course delivery,
  enrollments, assessments, marks, attainment thresholds, improvement
  plans) is defined with `schema="program"` — a marker, not a real schema
  name — and is physically created in a nested
  `tenant_<slug>__<program_code>` schema per program. See
  [ADR 0003](adr/0003-schema-per-program.md) for the full mechanism, the
  cross-schema-FK gotcha it documents, and why the split lands where it
  does (courses stay institution-shared so co-offered courses work).
- Tenant resolution middleware reads the institution from the subdomain
  (prod) or an `X-Institution-Slug` header (local dev), looks it up in
  `public.institutions`, and binds the session's `None` translate-map key.
  A second header, `X-Program-Code`, resolves and authorizes the `"program"`
  key for program-scoped endpoints (`app.services.rbac.get_program_context`
  / `get_program_scoped_db`). One set of models, no per-tenant or
  per-program code duplication; cross-tenant and cross-program leakage are
  structurally impossible — a session bound to one schema pair cannot see
  another's tables.
- Alembic runs **three independent migration chains**:
  - `alembic/public` — applied once, targets the `public` schema.
  - `alembic/tenant` — applied once *per institution schema* via
    `scripts/migrate_all_tenants.py`.
  - `alembic/program` — applied once *per program schema* via
    `scripts/migrate_all_programs.py`.
- Provisioning a new institution (`scripts/provision_tenant.py`, or
  `POST /api/v1/institutions`) = insert into `public.institutions` →
  `CREATE SCHEMA tenant_<slug>` → run the tenant Alembic chain → seed
  default roles/permissions/grading defaults. Provisioning a new program
  within an institution (`POST /org/programs`) = insert the `Program`
  registry row → `provision_program_schema()` (`CREATE SCHEMA
  tenant_<slug>__<code>` → run the program Alembic chain).

## 3. Two separate authentication planes

- **Tenant users** (`tenant_<slug>.users`) log in with email/password
  (`POST /auth/login`) or Google Sign-In (`POST /auth/google`, matches a
  verified Google email against an *existing* user row only — it never
  creates accounts). JWTs carry the institution slug so every subsequent
  request resolves the right tenant schema without needing the header on
  every call from the SPA.
- **Platform admins** (`public.platform_admins`) are a completely separate
  account space with their own login (`POST /platform-auth/login`), their
  own token type, and their own frontend app shell
  (`frontend/src/features/platform/`) — institution provisioning and an
  unscoped cross-institution raw-data console (§6). A platform admin is
  never a row in any tenant's `users` table and cannot be granted tenant
  permissions; the two identity spaces don't intersect.

## 4. RBAC (permission-based, never role-name-based)

- `permissions` are fixed, granular codes (`curriculum.view`,
  `outcome.approve`, `marks.enter`, `attainment.calculate`, …).
  Application code never checks `if role == "Dean"`.
- `roles` are configurable per tenant (seeded with a default set — several
  seeded `is_active=False` for a simpler assignable-roles list out of the
  box) and hold a set of `permissions` via `role_permissions`.
- `user_roles` assigns a role to a user **with an optional scope**
  (`scope_type` ∈ `institution | campus | school | department | program |
  course`, `scope_id` — `app.models.tenant.identity.ScopeType`), so e.g.
  "Program Coordinator" can be granted for one program only. The UI
  currently exposes institution-wide/program/course scoping (Institute
  Settings → Users & roles → per-scope tabs) — campus/school/department
  scoping exists at the model and permission-check level but has no
  dedicated picker yet. This is real and enforced, not just a schema field
  — `get_program_context` (§2) is the concrete place a `scope_type="program"`
  grant gates access to a whole program schema.
- A user can preview the system "as" one of their own roles (the active-role
  switcher, top-right of the app shell) — this isn't cosmetic nav-hiding:
  `hasPermission()` itself is restricted to that role's own permission set
  (`AuthUser.role_permissions`, computed server-side in `_build_current_user_read`),
  so switching to a lower-privilege role genuinely blocks access, not just
  hides links.
- A single FastAPI dependency, `require_permission("curriculum.approve")`
  (or `require_any_grant(...)` for "any one of several codes"), resolves the
  current user's effective permissions against the resource being accessed.
- A few read-only, non-sensitive lookups (`GET /org/programs`,
  `GET /org/academic-terms`) are deliberately open to any authenticated
  tenant user rather than gated behind a specific permission — every
  program-scoped page needs them just to populate a picker, and Faculty/
  Course Coordinator don't hold `program.view`/`academic_calendar.view`
  despite legitimately needing the program/term *names*. Real authorization
  for any actual mutation still happens at that action's own endpoint.

## 5. The raw-data console

A generic table browser/editor (`app/services/raw_data.py`,
`app/api/v1/endpoints/raw_data.py`) gated by four permission tiers, from
broadest to narrowest:
- `raw_data.manage_all` (platform admin only, separate unscoped console —
  §3) — every table, every institution.
- `raw_data.manage_institution` — every table, within one's own tenant.
- `raw_data.manage_scoped` — read/write within one's own program or course
  scope, resolved the same way `get_program_context` resolves a program
  grant.
- `raw_data.propose_scoped` — read + **propose** a change (insert/update/
  delete) rather than apply it directly; the proposal is staged as a
  `RawDataChangeRequest` row and only takes effect once a holder of a
  broader tier approves it (`raw_data.approve`).

This exists because accreditation data needs a full audit trail and a way
for a Program Coordinator to fix their own program's data without giving
them free rein over the institution's tables — the propose/approve tier is
the concrete mechanism for that middle ground.

## 6. The attainment engine (deliberately smaller than a full accreditation platform)

`app/services/attainment.py` calculates everything **on demand**, not as a
stored, versioned "run" the way a full accreditation platform might — see
that module's own docstring for the reasoning, and
`app/models/tenant/assessments/marks.py` for what was deliberately left
unbuilt (multi-methodology comparison, indirect/direct weighting,
PEO-level cascading). What's implemented:

- **Student → CO**: a student attains a CO if the % of that CO's mapped-
  question marks they scored is at least the course's configured
  `min_marks_percent`.
- **Course-level CO attainment**: a CO is attained if at least
  `min_students_percent` of *eligible* students attained it.
  Withdrawn/Incomplete-enrolled students' treatment (exclude vs. include)
  is itself configurable per course (`CourseAttainmentConfig.wi_treatment`).
- **CO → PO roll-up**: for each PO, a weighted average of every CO mapped to
  it (weighted by the CO-PO mapping's strength, and by each CO's own
  eligible-student count across however many sections it was assessed in).
- **Cohort/semester filtering**: an optional `batch_year` filter reuses
  `StudentProfile.batch_year` as the cohort key rather than a dedicated
  `Cohort` entity (see the service docstring for why); an optional
  `academic_term_id` filter narrows to one semester.
- **Program analytics dashboard**: course-level rollups (average CO
  attainment, COs below threshold, ranked weakest-first) and continuous-
  improvement counters, alongside the PO summary.
- **Student self-service dashboard**: the same numbers, scoped to one
  student's own enrollments only (`GET /marks/my-attainment` takes no
  student id from the client — it is always the caller's own data).
- **Continuous improvement**: when a CO misses its threshold, a
  faculty/coordinator can record an `ImprovementPlan` against it — propose
  → review (approve/reject) → implement, audit-logged at every step. No
  automatic background flagging job; the attainment report already marks a
  CO `is_attained=False` on every view, and the UI offers "create a plan"
  right there.

## 7. Reproducibility & data-integrity rules (as actually implemented)

- `student_marks` corrections overwrite `marks_obtained` in place — there is
  no immutable attempt-number history (an earlier, larger design sketch
  considered this; see the model's docstring for why it was scoped down —
  no accreditation-evidence audit requirement is driving that yet).
- Curriculum/course entities are versioned (`program_versions`,
  `course_versions`) rather than mutated in place — a curriculum change
  creates a new version row, so recalculating today's attainment never
  changes what an already-published prior version's PEOs/POs/COs meant.
- All approval-driven entities (PEOs, POs, COs, program versions,
  questions, assessments) share one workflow shape:
  `draft → submitted → reviewed → approved → published → archived`.
  `ImprovementPlan` deliberately does **not** reuse this enum — its
  lifecycle (`proposed → approved/rejected → implemented`) is a different
  shape (propose/approve/implement action-tracking, not a document being
  drafted and published) and forcing it into the shared enum would produce
  meaningless states.
- **Audit logging** happens in the service layer (`app/services/audit.py`,
  `write_audit_log`), not scattered across endpoints — every mutating
  endpoint that touches the tables above calls it explicitly with a
  before/after value pair, so every significant change (outcome edited,
  mapping changed, marks entered, assessment approved, improvement plan
  reviewed, raw-data change proposed/approved, …) has a row in
  `audit_logs`.

## 8. Implementation status

Implemented, with real Alembic migrations and live UI, as of this writing:
org structure, identity/RBAC (including scoped grants), multi-tenancy,
schema-per-program, course catalog + delivery (offerings/sections/faculty/
enrollments), grading policy, the BAETE v3.0 accreditation catalogue,
PEO/PO/CO definition and PEO-PO/CO-PO mapping, assessment definition
(types/rubrics/questions/assessments), marks entry, the full attainment
engine described in §6 (CO/PO/cohort/program-analytics/student-dashboard/
improvement-plan-workflow), the raw-data console (all four tiers), platform
admin + Google OAuth, and audit logging throughout.

Not implemented: stakeholder surveys (indirect attainment input), the
accreditation *submission* workflow (criteria/evidence upload — the
framework *catalogue* that workflow would reference already exists),
report-generation/export, and any AI-assisted features. See
`docs/DATABASE_PLAN.md` for the schema each of those would need and what,
if anything, already exists toward it.

## 9. Repository layout

```
OBEvolve/
├── docs/                  architecture, database plan, ADRs
├── backend/               FastAPI app, Alembic migrations (public/tenant/program), tests
├── frontend/               Vite + React + TS + Tailwind + shadcn/ui
├── scripts/                tenant/program provisioning, migration, demo-data helpers
└── .github/workflows/      CI (backend lint+test, frontend lint+build)
```

See `docs/DATABASE_PLAN.md` for the complete entity list and ERD.
