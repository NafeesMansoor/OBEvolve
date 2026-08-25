# ADR 0001: Schema-per-tenant multi-tenancy

## Status
Accepted

## Context
OBEvolve must serve multiple institutions with a hard requirement that "data
belonging to one institution must never leak into another" (spec §4). Three
options were considered:

1. Shared schema + `institution_id` column, isolation enforced only in
   application code.
2. Shared schema + `institution_id` column + PostgreSQL Row-Level Security (RLS)
   as defense-in-depth.
3. Schema-per-tenant: one PostgreSQL schema per institution, identical table
   structure, applied via SQLAlchemy's `schema_translate_map`.

## Decision
Schema-per-tenant (option 3).

## Rationale
- Strongest possible isolation guarantee: a query bug or missing filter cannot
  leak data across institutions, because a session bound to one tenant schema
  has no visibility into another schema's tables at all — isolation is enforced
  by the database's namespace mechanism, not by code discipline.
- A single set of SQLAlchemy models (no `schema=` hardcoded) works for every
  tenant via `execution_options(schema_translate_map={None: "tenant_<slug>"})`,
  so there is no per-tenant code duplication.
- Per-tenant backup/restore/delete is straightforward (a schema is a natural
  unit of operation).

## Trade-offs accepted
- Alembic migrations must run once per tenant schema
  (`scripts/migrate_all_tenants.py` loops sequentially over
  `public.institutions`). At pilot scale (tens of institutions) this is fine; if
  the platform grows to hundreds of tenants, this loop will need to become
  parallel/queued — not solved in Phase 1, flagged for later.
- Cross-tenant analytics/reporting (Super Admin dashboards spanning all
  institutions) requires iterating across schemas rather than a single query —
  acceptable since that is a rare, admin-only operation, not a hot path.
- One exception to "no hardcoded schema": tenant tables' `institution_id` FK
  points back at `public.institutions.id`, which does need an explicit
  `schema="public"` in that one column's `ForeignKey(...)` declaration.
