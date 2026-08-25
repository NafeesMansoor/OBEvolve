# OBEvolve — Architecture

## 1. Overview

OBEvolve is a multi-tenant Outcome-Based Education (OBE) and accreditation
management platform. It is built as a **modular monolith** (not microservices —
see [ADR 0001](adr/0001-schema-per-tenant.md) for the tenancy decision and
rationale) with a FastAPI backend and a React/TypeScript frontend, sharing one
PostgreSQL database via per-tenant schemas.

```
React + TS (Vite, Tailwind, shadcn/ui)
        │  REST (OpenAPI), JWT bearer
        ▼
FastAPI backend (modular monolith)
  ├─ core/         config, security, permissions
  ├─ api/v1/       versioned REST endpoints (thin controllers)
  ├─ services/     business logic (rbac, tenancy, audit, attainment engine*)
  ├─ models/       SQLAlchemy ORM (public schema + tenant schema)
  ├─ workers/      Celery tasks (attainment runs*, report generation*, notifications*)
  └─ middleware/   tenant resolution, audit logging
        │
        ▼
PostgreSQL (public schema + one schema per institution)
Redis (Celery broker + cache)
S3-compatible object storage (evidence files, reports)*
```
`*` = infrastructure wired now, feature logic built in a later phase (see §4).

## 2. Multi-tenancy: schema-per-tenant

- A **`public`** schema holds cross-tenant control data only: `institutions`
  (tenant registry) and `platform_admins` (the only role that spans institutions).
- Every other table (users, programs, courses, outcomes, assessments, marks,
  attainment results, evidence, …) is defined **once** in SQLAlchemy with no
  hardcoded schema, and is physically created in a `tenant_<slug>` schema per
  institution.
- Tenant resolution middleware reads the institution from the subdomain (prod) or
  an `X-Institution-Slug` header (local dev), looks it up in
  `public.institutions`, and binds the DB session for that request using
  SQLAlchemy's `execution_options(schema_translate_map={None: "tenant_<slug>"})`.
  One set of models, no per-tenant code duplication, and cross-tenant leakage is
  structurally impossible — a session bound to `tenant_a` cannot see `tenant_b`'s
  tables.
- Alembic runs **two independent migration chains**, split by SQLAlchemy
  `Base` (`PublicBase` vs `TenantBase`):
  - `alembic/public` — applied once, targets the `public` schema.
  - `alembic/tenant` — applied once *per tenant schema* via
    `scripts/migrate_all_tenants.py`, which loops over `public.institutions` and
    runs the tenant chain with `schema_translate_map` pointed at each schema.
- Provisioning a new institution (`scripts/provision_tenant.py`, or
  `POST /api/v1/institutions`) = insert into `public.institutions` →
  `CREATE SCHEMA tenant_<slug>` → run the tenant Alembic chain against it →
  seed default roles/permissions/Bloom levels for that tenant.

## 3. RBAC (permission-based, never role-name-based)

- `permissions` are fixed, granular codes (`curriculum.view`, `outcome.approve`,
  `marks.enter`, …). Application code never checks `if role == "Dean"`.
- `roles` are configurable per tenant (seeded with a default set) and hold a set
  of `permissions` via `role_permissions`.
- `user_roles` assigns a role to a user **with an optional scope**
  (`scope_type` ∈ {institution, campus, school, department, program},
  `scope_id`), so e.g. "Head of Department" can be granted for one department
  only.
- A single FastAPI dependency, `require_permission("curriculum.approve")`,
  resolves the current user's effective permissions against the resource being
  accessed.

## 4. Reproducibility & data-integrity rules

- Raw student performance (`student_performance`) is **never overwritten** by
  attainment calculation; corrections are new rows, not updates.
- Every attainment calculation is an immutable `attainment_runs` row capturing
  methodology + version + parameters + timestamp + executor; results point at
  the run that produced them.
- Curriculum/course entities are versioned (`program_versions`,
  `course_versions`) rather than mutated in place.
- All approval-driven entities share one workflow shape:
  `draft → submitted → reviewed → approved → published → archived`.

## 5. Development phases

Phase 1 (Foundation) is fully implemented: project scaffolding, auth, RBAC,
multi-tenancy, institution/campus/school/department structure, migrations, audit
logging.

Phases 2–10 (Academic Structure, OBE Engine, Course Delivery, Assessment,
Attainment Engine, Surveys & Continuous Improvement, Accreditation, Analytics,
AI) have their module directories scaffolded with a `README.md` describing scope,
but no implementation yet — see `docs/DATABASE_PLAN.md` for the full data model
these phases will build against, and the spec's own phase breakdown for
implementation order.

## 6. Repository layout

```
OBEvolve/
├── docs/                  architecture, database plan, ADRs
├── backend/               FastAPI app, Alembic migrations, tests
├── frontend/              Vite + React + TS + Tailwind + shadcn/ui
├── scripts/               tenant provisioning / migration helpers
└── .github/workflows/     CI (backend lint+test, frontend lint+build)
```

See `docs/DATABASE_PLAN.md` for the complete entity list and ERD.
