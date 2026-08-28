# Deploying to Render

This repo includes a [Render Blueprint](https://render.com/docs/blueprint-spec)
(`render.yaml` at the repo root) that provisions everything OBEvolve needs:
a managed Postgres database, the FastAPI backend, and the React frontend as
a static site. This doc is the rest of the walkthrough — the parts a
Blueprint can't do for you (secrets, the very first login, creating your
first institution).

Every step below has been dry-run against a real, completely empty database
before being written down — the sequence is exactly what a fresh deploy needs.

## 1. Push this repo to GitHub (if you haven't)

Render deploys from a GitHub (or GitLab) repo. If you're already reading
this from a clone, you're set.

## 2. Create the Blueprint on Render

1. [render.com](https://render.com) → **New** → **Blueprint**.
2. Connect the GitHub repo. Render finds `render.yaml` automatically and
   shows you three resources: `obevolve-postgres`, `obevolve-backend`,
   `obevolve-frontend`.
3. Click **Apply**. Render provisions the database and kicks off both
   service builds. First build takes a few minutes (Python deps + `npm ci`).

The backend's `startCommand` runs the public-schema migration
(`alembic -c alembic/public/alembic.ini upgrade head`) before starting
`uvicorn` every time it boots — so the database schema is always current,
with no separate migration step for you to remember. This only creates the
`institutions`/`platform_admins` tables (the ones shared across every
tenant); each institution's own tables are created automatically when you
create that institution in step 5.

## 3. Wire the two services' URLs together

`render.yaml` leaves `BACKEND_CORS_ORIGINS`, `FRONTEND_ORIGIN`, and
`VITE_API_BASE_URL` as manual (`sync: false`) placeholders, because Render
assigns each service's final `*.onrender.com` hostname at creation time —
it isn't knowable before that first deploy, and if `obevolve-backend` or
`obevolve-frontend` is already taken by someone else on Render, yours gets a
suffix.

Once both services have deployed once:

1. Open **obevolve-backend** → **Environment** → note the URL shown at the
   top of the service page (e.g. `https://obevolve-backend.onrender.com`).
2. Open **obevolve-frontend** → **Environment** → note its URL the same way.
3. On **obevolve-backend** → **Environment**, set:
   - `BACKEND_CORS_ORIGINS` = `["<frontend URL>"]` (exact JSON array syntax,
     e.g. `["https://obevolve-frontend.onrender.com"]`)
   - `FRONTEND_ORIGIN` = `<frontend URL>` (used only to build the link inside
     password-reset emails)
4. On **obevolve-frontend** → **Environment**, set:
   - `VITE_API_BASE_URL` = `<backend URL>/api/v1`
5. Save — each save triggers a redeploy of that service (the frontend one
   rebuilds since Vite env vars are baked in at build time, not read at
   runtime).

## 4. Get your data onto the Render database

Two ways to get there — pick one.

### Option A: restore your existing local database

Recommended if you already have real/rich data locally — this is what
carries over the fully populated demo tenant (real marks, calculated
attainment, improvement plans in every status), not just the bare
`seed_demo` skeleton.

1. On the Render dashboard, open **obevolve-postgres** → **Connect** → copy
   the **External Database URL** (starts `postgresql://`, reachable from
   outside Render — the free tier supports this).
2. From your machine, with a dump already in hand (see below for how to make
   one), run:
   ```bash
   psql "<External Database URL>" < backups/obevolve_demo_<timestamp>.sql
   ```
   The dump is generated with `--clean --if-exists`, so it `DROP`s and
   recreates everything it touches — safe to run whether the backend has
   already booted (and created empty `public.institutions`/
   `platform_admins` tables via its own migration) or not. It carries over
   whichever `public.platform_admins` row(s) exist locally too, so there's
   no separate bootstrap-admin step — log in with the same email/password
   you already use locally.
3. To make that dump from your local dev Postgres (adjust the schema names
   to whichever institution(s)/tenant(s) you actually want to bring over —
   this example is the `demo` tenant only):
   ```bash
   pg_dump -U obevolve -d obevolve --clean --if-exists --no-owner --no-privileges \
     --schema=public --schema=tenant_demo --schema='tenant_demo__bscse' --schema='tenant_demo__bsse' \
     > backups/obevolve_demo_$(date +%Y%m%d_%H%M%S).sql
   ```
   (`backups/` is already gitignored — this file has real user data in it,
   including password hashes; never commit it.) If your local Postgres has
   *other* institutions you don't want on Render too (e.g. this repo's own
   dev database also has a `ulab-cse` tenant), leave their schemas out of
   `--schema=`; their `public.institutions` row still comes along either way
   since `public` is dumped whole, but with no matching tenant schema behind
   it, any request for that slug will error instead of serving real data —
   harmless, but `DELETE FROM public.institutions WHERE slug = '...';` after
   restoring cleans it up if that bothers you.
4. Skip step 5 below entirely — the institution(s), users, and data are
   already there.

### Option B: seed fresh demo data instead (no local data to bring over)

There's no signup page for creating the first platform admin on purpose — a
platform admin can create and manage every institution in the deployment,
so it isn't something to expose over HTTP without its own bootstrap-auth
story. Create it directly against the database instead:

1. On **obevolve-backend**, open the **Shell** tab (or **Jobs** → **Run
   Job** if Shell isn't available on your plan).
2. Run:
   ```bash
   python scripts/create_platform_admin.py --email you@example.com --password 'choose-one' --name "Your Name"
   ```
   Re-running it with the same email later just updates the password —
   it's safe to use for a reset.
3. Continue to step 5.

## 5. Create your first institution (Option B only — skip if you restored data in step 4)

1. Go to `<frontend URL>/platform-login` and sign in with the email/password
   from step 4.
2. **Create institution**. Fields:
   - **Slug** — must exactly match `VITE_INSTITUTION_SLUG` in the frontend's
     env vars (`render.yaml` defaults both to `demo`). This is how the
     backend knows which tenant a request belongs to
     (`backend/app/middleware/tenancy.py` reads it from the
     `X-Institution-Slug` header the frontend sends on every request — this
     deployment doesn't use per-tenant subdomains, so one frontend
     deployment serves exactly one institution's slug).
   - **Seed demo data** — check this the first time. Without it, the
     institution is created with no users at all and nothing can log in to
     it (there's currently no self-serve "invite the first admin" flow for a
     freshly created institution — filing that as a product gap, not
     something this deploy doc can paper over). With it checked, you get a
     working login: `admin@demo.obevolve.dev` / `ChangeMe123!` — **change
     that password immediately** (Profile → after logging in) since it's a
     hardcoded seed default, plainly visible in this repo's source. Note
     this only runs `app.seed.demo_institution` (one admin user, empty
     otherwise) — it is *not* the same as Option A's fully populated dataset;
     run `python scripts/populate_demo_data.py` from the backend Shell
     afterward against this institution if you want the richer dataset
     without a local database to restore from.
3. Log in to `<frontend URL>/login` with that account.

If you later want a *second*, non-demo institution, it needs a different
slug, which means a different `VITE_INSTITUTION_SLUG` — i.e. a second
frontend static site pointed at the same backend. The subdomain-resolution
path in `middleware/tenancy.py` is the real multi-tenant answer for
"many institutions, one frontend deployment," but wiring up wildcard DNS +
per-tenant subdomains on Render is out of scope for this doc.

## 6. File uploads — read this before relying on them in production

Render's free/starter web services have an **ephemeral filesystem**: every
deploy (including ones Render triggers itself, e.g. for a env var change)
wipes anything written to local disk. Assessment document uploads
(question papers, moderation/compliance forms, scripts, CEP documents —
`backend/app/services/storage.py`) fall back to local disk when no S3
config is set, which is fine for *trying the feature out* but will silently
lose files on the next deploy otherwise.

For real use, set `S3_ENDPOINT_URL` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` /
`S3_BUCKET_NAME` on the backend service to a real S3-compatible bucket
(AWS S3, Cloudflare R2, Backblaze B2 all work — `storage.py` just needs an
S3-compatible endpoint). No code changes needed; `storage.py` already
prefers S3 over local disk whenever those three are set.

## 7. What's on the free plan, and what isn't

- Render's free Postgres expires after 30 days and free web services spin
  down after 15 minutes idle (cold-start delay on the next request) — fine
  for evaluating the app, not for anything real. Upgrade the relevant
  service/database plan in the Render dashboard when you're ready; nothing
  in `render.yaml` locks you to `free`.
- Redis/Celery (`docker-compose.yml`'s `redis` service,
  `backend/app/workers/celery_app.py`) is **not** part of this Blueprint —
  nothing in the request path uses it yet (see that file's docstring), so
  there's nothing to deploy for it. Add a Render Key Value instance and a
  worker service if/when a real Celery task exists.

## Troubleshooting

- **`ModuleNotFoundError: psycopg2` on backend boot** — you (or Render)
  overwrote `DATABASE_URL` with a bare `postgres://`/`postgresql://` URL.
  `backend/app/core/config.py` normalizes this automatically as of this
  Blueprint, but if you're running an older checkout, either update, or
  rewrite the URL's scheme to `postgresql+psycopg://` by hand.
- **Frontend loads but every request 400s "Institution could not be
  determined"** — `VITE_INSTITUTION_SLUG` is unset/wrong, or doesn't match
  an institution's `slug` in the database yet (step 5 not done).
- **CORS errors in the browser console** — `BACKEND_CORS_ORIGINS` on the
  backend doesn't include the frontend's exact URL (scheme + host, no
  trailing slash), or you edited it but the backend hasn't redeployed yet.
