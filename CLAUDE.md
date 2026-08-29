# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

OBEvolve is a multi-tenant Outcome-Based Education (OBE) and accreditation management platform:
curriculum design → outcome mapping → course delivery → assessment → attainment calculation →
continuous improvement → accreditation reporting. Backend: FastAPI + SQLAlchemy 2.x + Alembic
(Python 3.11+). Frontend: React 19 + TypeScript + Vite + Tailwind + shadcn/ui. Database: one
Postgres instance, schema-per-institution with schema-per-program nested inside it.

Full architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Full data model:
[docs/DATABASE_PLAN.md](docs/DATABASE_PLAN.md). Deploying: [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md).

## Commands

### Backend (`backend/`, venv at `backend/.venv`)

```bash
source .venv/bin/activate
uvicorn app.main:app --reload              # dev server, http://localhost:8000
ruff check app/ scripts/                   # lint (line-length 100, see pyproject.toml)
mypy app/                                  # type check
pytest                                     # full suite (testpaths = tests/, asyncio_mode = auto)
pytest tests/unit/test_rbac.py             # one file
pytest tests/unit/test_rbac.py::test_scoped_grant_only_satisfies_matching_scope  # one test
pytest tests/integration/                  # unit/ vs integration/ — see backend/tests/
```

Migrations are **three independent Alembic chains**, not one — see "Multi-tenancy" below before
touching any of them:

```bash
alembic -c alembic/public/alembic.ini upgrade head                 # once, public schema
alembic -c alembic/tenant/alembic.ini -x schema=tenant_<slug> upgrade head
alembic -c alembic/program/alembic.ini -x institution_schema=tenant_<slug> \
  -x program_schema=tenant_<slug>__<program_code> upgrade head
```

New migration: `alembic -c alembic/<public|tenant|program>/alembic.ini revision -m "..."` (no
`--autogenerate` — this repo hand-writes migrations; see any file under `alembic/*/versions/` for
the established style, including the `_target_schema()` / raw-SQL-`ALTER TABLE` workaround needed
because `op.add_column`/`op.drop_column` don't reliably honor `schema_translate_map`).

### Frontend (`frontend/`)

```bash
npm run dev      # http://localhost:5173
npm run build    # tsc -b && vite build — type errors fail the build
npm run lint     # eslint .
```

No frontend test runner is configured yet (no vitest/jest) — `tsc -b` + `eslint` are the only
automated checks.

### Everything via Docker Compose

`docker-compose.yml` exists but has no committed Dockerfiles for `backend`/`frontend` yet — don't
assume `docker compose up` works until those exist.

## Multi-tenancy — read before touching models, migrations, or any `X-*` header

- `public` schema: `institutions` + `platform_admins` only (cross-tenant control data).
- Institution-shared tables (users, RBAC, org structure, course catalog, grading, accreditation
  catalogue, audit log): one SQLAlchemy definition, no hardcoded schema, physically created in
  `tenant_<slug>` per institution.
- Program-specific tables (curricula/PEOs/POs, delivery, enrollments, assessments, marks,
  attainment config, improvement plans): `__table_args__ = {"schema": "program"}` — a translate-map
  marker, not a literal schema name — physically created in `tenant_<slug>__<program_code>`.
- Every session is bound via `execution_options(schema_translate_map=...)` on one shared engine,
  not a per-tenant engine. `X-Institution-Slug` (prod: subdomain) resolves the `None` key;
  `X-Program-Code` additionally resolves the `"program"` key for program-scoped endpoints
  (`get_program_scoped_db`). A session bound to one schema pair structurally cannot see another's.
- RBAC is **permission-code-based, never role-name-based** — `require_permission("curriculum.approve")`,
  never `if role.name == "Dean"`. Codes are fixed (`backend/app/core/permissions.py`); roles are
  configurable per tenant and just hold a set of codes (`backend/app/seed/default_roles.py`
  documents the default set and scope-type conventions). See
  [docs/ACCESS_MAP.md](docs/ACCESS_MAP.md) (or the same data as a browsable
  [interactive artifact](https://claude.ai/code/artifact/f984e975-d442-4367-8a1e-df55b14d53b8))
  for the full per-role menu/tab/read-write breakdown if you need to reason about who can see or
  do what.
- Two separate, non-overlapping auth planes: tenant users (`/auth/login`) vs. platform admins
  (`/platform-auth/login`, `public.platform_admins`, own frontend shell under
  `frontend/src/features/platform/`). A platform admin is never a tenant user row.
- `WorkflowStatus` (draft→submitted→reviewed→approved→published→archived,
  `backend/app/db/base.py`) is the shared lifecycle for outcomes/versions/questions/assessments,
  advanced one step at a time via a dedicated `POST .../{id}/advance` endpoint per resource — not a
  generic PATCH-with-status-field. A handful of models (`RawDataChangeRequest`,
  `ImprovementPlan`, `AssessmentDocument`) deliberately use a smaller, purpose-built
  pending/approved/rejected status instead, because "propose → approve" is a different shape than
  a multi-stage document lifecycle — don't force those onto `WorkflowStatus`, and don't reuse their
  narrower status for something that actually is a draft-to-published document.

## Design system

[design-system/obevolve/MASTER.md](design-system/obevolve/MASTER.md) is the source of truth for
color tokens, typography, spacing, and the per-page redesign checklist — read it before making any
visual change to the frontend. It also documents where the light/dark theme toggle
(`next-themes`) lives and the Bloom's-Level/CO-mapping convention for question authoring.

## Semantic code intelligence (CodeCortex)

This repo is indexed with [CodeCortex](https://github.com/NafeesMansoor/CodeCortex), a semantic
code-graph tool (tree-sitter → Code Property Graph → embeddings → clustering/centrality →
retrieval) — reach for it instead of a plain grep sweep when a question spans both languages
(backend + frontend), needs "what calls/imports this" or blast-radius reasoning, or is a fuzzy
"where is the code that does X" question rather than an exact-string search.

**Setup** (already done in this repo, documented here so it's not re-discovered): the CLI lives in
its own clone + venv at `tools/codecortex/` (gitignored — it's a vendored dev tool, not an OBEvolve
dependency; `backend/.venv` is unrelated). Indexing config is `codecortex.yaml` at the repo root.
The generated graph snapshot is `.codecortex/graph.json` (gitignored, regenerable, ~2.8 MB as of
the last reindex — 259 files, 2124 nodes, 12296 edges).

**Every invocation needs these two env vars on macOS**, or `query`/`impact` segfault (a real
PyTorch/FAISS OpenMP duplicate-library conflict, not flaky — `index` alone doesn't need them since
it never loads the retrieval/embedding-search path):

```bash
export KMP_DUPLICATE_LIB_OK=TRUE
export OMP_NUM_THREADS=1
```

```bash
CC=tools/codecortex/.venv/bin/codecortex   # shorthand used below

# Reindex after a large batch of changes (not needed for small edits — query
# rebuilds on the fly, just slower). Takes ~35-40s.
$CC index . --config codecortex.yaml --mode cpg --enable-embeddings --enable-clustering \
  --save-snapshot .codecortex/graph.json

# Natural-language semantic search across backend + frontend
$CC query --query "assessment document pending review" --target . --config codecortex.yaml

# Blast radius of changing a function/class
$CC query --impact require_permission --target . --config codecortex.yaml

# Interactive graph explorer at http://localhost:7979 (no --config flag —
# visualize doesn't accept one; it builds its own lighter default index)
$CC visualize .
```

**Two real bugs in the CodeCortex install were found and fixed while setting this up** (patched
locally under `tools/codecortex/`, not yet upstreamed — mention it if you're touching that tool
again): (1) `pipeline/context_builder.py`'s file walker only globbed one hardcoded extension per
language (`.ts`, `.js`), silently dropping every `.tsx`/`.jsx` file — for this repo that meant the
entire React component tree was invisible to the index; fixed to expand each parser's full
`.extensions` list. (2) `core/parsers/typescript_parser.py` used the plain `typescript` tree-sitter
grammar (no JSX support) for `.tsx` files too; fixed to pick the `tsx` grammar variant by
extension. If `tools/codecortex` gets re-cloned or updated, re-check whether these are fixed
upstream before assuming they still need the local patch.
