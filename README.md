# OBEvolve

A multi-tenant Outcome-Based Education (OBE) and accreditation management
platform: curriculum design → outcome mapping → course delivery → assessment →
attainment calculation → stakeholder feedback → continuous improvement →
accreditation reporting.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the system design and
[docs/DATABASE_PLAN.md](docs/DATABASE_PLAN.md) for the full data model.

**Status**: Phase 1 (Foundation) — project scaffolding, auth, RBAC,
multi-tenancy, institution/campus/school/department structure, migrations,
audit logging. Everything else is scaffolded (empty module folders +
`README.md` per module) but not yet implemented — see each module's phase
number and `docs/DATABASE_PLAN.md`.

## Stack

- Backend: FastAPI + SQLAlchemy 2.x + Alembic, Python 3.11+
- Frontend: React + TypeScript + Vite + Tailwind CSS + shadcn/ui
- Database: PostgreSQL 16 (schema-per-tenant multi-tenancy)
- Cache / queue broker: Redis (Celery wired, no tasks yet)
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
creates its tenant schema and runs the tenant-schema migration + seed data):

```bash
alembic -c alembic/public/alembic.ini upgrade head
python -m scripts.provision_tenant --slug demo --name "University Demo" --seed-demo
```

Start the API:

```bash
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Demo login (seeded by `--seed-demo`): `admin@demo.obevolve.local` /
`ChangeMe123!`, header `X-Institution-Slug: demo`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173

### 5. Or run everything via Docker Compose

```bash
docker compose up -d
```

## Tests

```bash
cd backend && source .venv/bin/activate && pytest
```

## Repository layout

```
OBEvolve/
├── docs/            architecture, database plan, ADRs
├── backend/         FastAPI app, Alembic migrations (public/ + tenant/), tests
├── frontend/         Vite + React + TS + Tailwind + shadcn/ui
├── scripts/          tenant provisioning / migration helpers
└── .github/workflows/  CI (backend lint+test, frontend lint+build)
```
