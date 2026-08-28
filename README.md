# OBEvolve

A multi-tenant Outcome-Based Education (OBE) and accreditation management
platform: curriculum design → outcome mapping → course delivery → assessment →
attainment calculation → continuous improvement → accreditation reporting.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the system design and
[docs/DATABASE_PLAN.md](docs/DATABASE_PLAN.md) for the full data model.

**Status**: org structure, identity/RBAC (including scoped role grants),
multi-tenancy with schema-per-program, the full course catalog + delivery
pipeline, grading policy, the BAETE v3.0 accreditation catalogue, PEO/PO/CO
definition and mapping, assessment definition, marks entry, the full
attainment engine (CO/PO/cohort/program-analytics/student-dashboard/
improvement-plan workflow), the raw-data console, and platform admin +
Google OAuth are all implemented with real migrations and live UI. Not yet
built: stakeholder surveys, the accreditation *submission* workflow
(criteria/evidence upload — the framework catalogue it would reference
already exists), report generation, and AI features. See
`docs/ARCHITECTURE.md` §8 and `docs/DATABASE_PLAN.md` for exactly what's
implemented vs. still planned, table by table.

## Stack

- Backend: FastAPI + SQLAlchemy 2.x + Alembic, Python 3.11+
- Frontend: React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- Database: PostgreSQL 16 — schema-per-institution, with schema-per-program
  nested inside it (see [ADR 0001](docs/adr/0001-schema-per-tenant.md) and
  [ADR 0003](docs/adr/0003-schema-per-program.md))
- Redis/Celery are wired (`docker-compose.yml`, `app/workers/celery_app.py`)
  but nothing in the product uses them yet — every calculation runs
  synchronously, on demand, in the request that asks for it
- Local orchestration: Docker Compose

## Getting started (local development)

### 1. Environment

```bash
cp .env.example .env
# edit .env if you want non-default credentials
```

### 2. Start Postgres + Redis

```bash
docker compose up -d postgres redis
```

### 3. Backend (venv)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Run the public-schema migration, then provision the demo institution (this
creates its tenant schema and runs the tenant-schema migration + seed
data — an admin user and a minimal org skeleton):

```bash
alembic -c alembic/public/alembic.ini upgrade head
python -m scripts.provision_tenant --slug demo --name "University Demo" --seed-demo
```

Then fill it with a full working dataset — courses, curricula, faculty,
students, enrollments, marks, and a second program, so every feature has
something real to click through (idempotent, safe to re-run):

```bash
cd ..  # repo root — the script resolves backend/ itself
python -m scripts.populate_demo_data
```

Start the API:

```bash
cd backend
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 4. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

- App: http://localhost:5173 (points at the `demo` tenant by default via
  `VITE_INSTITUTION_SLUG` in `frontend/.env` — change it, or run a second
  `vite --mode <name>` instance with its own `.env.<name>`, to point at a
  different tenant without losing the first one's session)

### 5. Or run everything via Docker Compose

```bash
docker compose up -d
```

## Demo login credentials

All seeded by `scripts/populate_demo_data.py` against the `demo` tenant
(`X-Institution-Slug: demo`). Every non-admin user shares one password:
**`Demo@12345`**. The tenant has two programs — **BSCSE** (fully populated:
marks entered, attainment calculated, improvement plans in every status)
and **BSSE** (a second, deliberately smaller program with no marks entered
yet, to show what an unassessed program looks like) — switch between them
with the program selector in the top-right of the app once logged in.

| Role | Email | Notes |
|---|---|---|
| Institution Administrator | `admin@demo.obevolve.dev` | password `ChangeMe123!` — seeded by `--seed-demo`, not the population script |
| Faculty | `alice.rahman@demo.obevolve.dev` | teaches CS101, CS310, and both BSSE courses |
| Faculty | `bob.islam@demo.obevolve.dev` | teaches CS201, CS150 |
| Faculty + Course Coordinator + Program Coordinator (scoped to BSCSE) | `carol.chowdhury@demo.obevolve.dev` | reviews/approves improvement plans; also coordinates CS301 |
| Student | `student001@demo.obevolve.dev` … `student015@demo.obevolve.dev` | BSCSE, batch 2022 — `student001` (Rafi Ahmed) has a full mix of attained/not-attained COs, good for exercising the student dashboard |
| Student | `bsse.student001@demo.obevolve.dev` … `bsse.student005@demo.obevolve.dev` | BSSE, batch 2023, no marks entered yet |

Platform admin (cross-institution provisioning + unscoped raw-data console,
separate login at a separate URL — see `ARCHITECTURE.md` §3): `admin@nafees.info`.

The real ULAB CSE tenant (`X-Institution-Slug: ulab-cse`) is a separate,
non-demo tenant with actual institutional data — see
`docs/obevolve_ulab_cse_setup.md`; its credentials aren't listed here.

## Accessing the database from the terminal

Local Postgres runs in Docker (`docker compose up -d postgres`), publishing
port 5432. Two ways in:

**Via `docker exec` (no local `psql` needed):**
```bash
docker compose exec postgres psql -U obevolve -d obevolve
```

**Via a local `psql` client**, using the credentials from `backend/.env`
(defaults shown — `POSTGRES_USER=obevolve`, `POSTGRES_PASSWORD=change-me`,
`POSTGRES_DB=obevolve`):
```bash
psql "postgresql://obevolve:change-me@localhost:5432/obevolve"
```

Once connected, remember this is schema-per-tenant-per-program (§ADR 0001,
§ADR 0003) — every institution and program has its **own schema**, not a
shared table with a tenant column:

```sql
-- List every schema (institution + program schemas, plus public)
\dn

-- e.g. for the demo tenant's two programs:
--   public
--   tenant_demo                (institution-shared: users, courses, roles, ...)
--   tenant_demo__bscse         (BSCSE program-specific: peos, assessments, marks, ...)
--   tenant_demo__bsse          (BSSE program-specific)

-- List tables in one schema
\dt tenant_demo.*
\dt "tenant_demo__bscse".*        -- quote schema names containing __ or -

-- Query a table in a specific schema (always schema-qualify — there is no
-- "current tenant" the way the app's per-request session binds one)
SELECT id, code, title FROM tenant_demo.courses LIMIT 10;
SELECT code, statement, status FROM "tenant_demo__bscse".program_outcomes;

-- Find which schema an institution/program maps to
SELECT slug, schema_name FROM public.institutions;
SELECT code, name FROM tenant_demo.programs;  -- schema is tenant_<slug>__<code, lowercased>
```

Password hashes are bcrypt (`app.core.security.hash_password`) — there is
no way to read a plaintext password back out of the database; use the demo
credentials above, or reset one via `app.core.security.hash_password("...")`
in a Python shell and an `UPDATE ... SET password_hash = :hash`.

## Tests

```bash
cd backend && source .venv/bin/activate && pytest
```

## Repository layout

```
OBEvolve/
├── docs/            architecture, database plan, ADRs
├── backend/         FastAPI app, Alembic migrations (public/tenant/program), tests
├── frontend/        Vite + React + TS + Tailwind + shadcn/ui
├── scripts/         tenant/program provisioning, migration, demo-data helpers
└── .github/workflows/  CI (backend lint+test, frontend lint+build)
```
