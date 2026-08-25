# OBEvolve — Frontend

Vite + React + TypeScript + Tailwind CSS + shadcn/ui frontend for OBEvolve, a
multi-tenant Outcome-Based Education / accreditation platform. See the root
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) for the overall system and
[`docs/DATABASE_PLAN.md`](../docs/DATABASE_PLAN.md) for the full data model
and phase roadmap.

This package currently implements **Phase 1 (Foundation)** only: the app
shell, login, protected routing, and a placeholder dashboard. Everything else
(`src/features/curriculum`, `outcomes`, `assessments`, `attainment`,
`surveys`, `accreditation`) is a stub directory pointing at the phase that
will implement it.

## Getting started

```bash
cp .env.example .env   # point VITE_API_BASE_URL at your backend
npm install
npm run dev
```

## Scripts

- `npm run dev` — start the Vite dev server (http://localhost:5173)
- `npm run build` — type-check (`tsc -b`) then production build
- `npm run lint` — ESLint
- `npm run preview` — preview the production build locally

## Structure

- `src/app/` — routing, the authenticated app shell (sidebar/topbar layout),
  and the protected-route guard.
- `src/features/` — one directory per product module. Only `auth` and
  `dashboard` have real implementations in Phase 1.
- `src/lib/api-client.ts` — axios instance: attaches `Authorization` and
  `X-Institution-Slug` headers, retries once on 401 via `/auth/refresh`.
- `src/lib/auth-context.tsx` — session state (current user, tokens) and
  `login`/`logout` actions. See the tradeoff comment at the top of that file
  for how tokens are stored in a pure SPA with no same-origin backend proxy.
- `src/components/ui/` — shadcn/ui primitives (Radix + CVA), generated via
  the shadcn CLI (`components.json`) rather than hand-rolled.

## Backend contract

Talks to the FastAPI backend described in `docs/ARCHITECTURE.md`, base URL
from `VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`). Every
request carries `X-Institution-Slug` in local dev (see
`VITE_INSTITUTION_SLUG` in `.env.example`); production resolves the tenant
from the subdomain instead.
