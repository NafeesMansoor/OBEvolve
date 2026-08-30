"""`provision_tenant()` — the one function that creates a new institution.

Steps (ARCHITECTURE.md §2):
1. Insert the `institutions` row (public schema) and commit — the tenant
   registry entry must be durable before we start creating database objects
   that reference it.
2. `CREATE SCHEMA tenant_<slug>` (transactional DDL — Postgres, unlike most
   RDBMSes, rolls this back cleanly on error).
3. Run the tenant Alembic chain against that schema in-process.
4. Seed default permissions + roles + assessment types (and demo data, if
   requested).

Steps 2-4 are not nested inside the step-1 transaction: Alembic manages its
own transaction per migration and cannot straightforwardly share one with an
open ORM session. Instead, failure at any of steps 2-4 triggers explicit
compensating cleanup (drop the schema, delete the institutions row) so a
failed provisioning attempt doesn't leave an orphaned tenant registry entry
pointing at a schema that was never fully migrated.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_engine, session_scope
from app.models.public.institution import Institution
from app.seed.assessment_defaults import seed_default_assessment_types
from app.seed.bloom_defaults import seed_default_bloom_levels
from app.seed.course_file_defaults import seed_default_course_file_types
from app.seed.default_permissions import seed_default_permissions
from app.seed.default_roles import seed_default_roles
from app.seed.demo_institution import seed_demo_data
from app.seed.mapping_defaults import seed_default_mapping_scale

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_TENANT_ALEMBIC_INI = _BACKEND_ROOT / "alembic" / "tenant" / "alembic.ini"
_PROGRAM_ALEMBIC_INI = _BACKEND_ROOT / "alembic" / "program" / "alembic.ini"

# The API layer (schemas/institution.py) validates this same pattern, but the
# schema name derived from it is interpolated into raw DDL (`CREATE SCHEMA
# "..."`) below, and provision_tenant() is also called directly from
# scripts/provision_tenant.py, which bypasses the Pydantic schema entirely —
# so the check is repeated here as the one place that actually matters.
_SLUG_PATTERN = re.compile(r"^[a-z0-9-]+$")

# Same pattern, reused for program codes when they're interpolated into
# `CREATE SCHEMA "..."` DDL by provision_program_schema() below. Program.code
# itself has no such constraint at the schema layer (it's a short display
# code like "BSCSE", not a URL slug) — this check runs on the lowercased
# code right before it's used to derive a schema name, same defense-in-depth
# reasoning as _SLUG_PATTERN above.
_PROGRAM_CODE_PATTERN = re.compile(r"^[a-z0-9-]+$")


class InvalidSlugError(Exception):
    """Raised when a slug would produce an unsafe/invalid schema identifier."""


class InvalidProgramCodeError(Exception):
    """Raised when a program code would produce an unsafe/invalid schema identifier."""


class TenantAlreadyExistsError(Exception):
    """Raised when the requested slug or derived schema name is already taken."""


class TenantProvisioningError(Exception):
    """Raised when schema creation, migration, or seeding fails. The caller's
    partial state (schema, institutions row) has already been cleaned up."""


class ProgramProvisioningError(Exception):
    """Raised when a program schema's creation or migration fails."""


def run_program_migrations(institution_schema: str, program_schema: str) -> None:
    """Run the program Alembic chain against one program schema, in-process.

    Used both by `provision_program_schema` (new program) and
    `scripts/migrate_all_programs.py` (existing programs picking up new
    migrations).
    """
    cfg = Config(str(_PROGRAM_ALEMBIC_INI))
    cfg.attributes["institution_schema"] = institution_schema
    cfg.attributes["program_schema"] = program_schema
    command.upgrade(cfg, "head")


def provision_program_schema(institution_schema: str, program_code: str) -> str:
    """Create and migrate one program's schema
    (`<institution_schema>__<program_code>`, per
    docs/adr/0003-schema-per-program.md). Returns the program schema name.

    Called from the program-creation endpoint (`POST /org/programs`) right
    after the `Program` row is inserted — mirrors `provision_tenant`'s
    schema-then-migrate sequencing. `CREATE SCHEMA IF NOT EXISTS` + an
    idempotent `alembic upgrade head` means this is also safe to re-run
    against an already-provisioned program (used by
    `scripts/migrate_all_programs.py`).

    No seed step here (unlike `provision_tenant`): everything a program
    schema's tables reference (permissions, roles, the default mapping
    scale, assessment types) is institution-shared and was already seeded
    once when the institution itself was provisioned.
    """
    slug = program_code.strip().lower()
    if not _PROGRAM_CODE_PATTERN.match(slug):
        raise InvalidProgramCodeError(
            f"Invalid program code {program_code!r}: only lowercase letters, "
            "digits, and hyphens are allowed (after lowercasing)."
        )
    program_schema = f"{institution_schema}__{slug}"

    engine = get_engine()
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{program_schema}"'))

        run_program_migrations(institution_schema, program_schema)
    except Exception as exc:
        logger.exception(
            "tenancy.program_provisioning_failed",
            extra={"institution_schema": institution_schema, "program_code": slug},
        )
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{program_schema}" CASCADE'))
        raise ProgramProvisioningError(
            f"Provisioning program schema {program_schema!r} failed: {exc}"
        ) from exc

    logger.info(
        "tenancy.program_provisioned",
        extra={"institution_schema": institution_schema, "program_schema": program_schema},
    )
    return program_schema


def run_tenant_migrations(schema_name: str) -> None:
    """Run the tenant Alembic chain against one schema, in-process.

    Used both by `provision_tenant` (new tenant) and
    `scripts/migrate_all_tenants.py` (existing tenants picking up new
    migrations).
    """
    cfg = Config(str(_TENANT_ALEMBIC_INI))
    cfg.attributes["schema_name"] = schema_name
    command.upgrade(cfg, "head")


def _slugify_schema(slug: str) -> str:
    return f"{settings.tenant_schema_prefix}{slug}"


def provision_tenant(
    db: Session,
    *,
    name: str,
    code: str,
    slug: str,
    contact_email: str,
    subscription_plan: str | None = None,
    timezone: str = "UTC",
    seed_demo: bool = False,
) -> Institution:
    """Create a new institution end-to-end. `db` must be a session bound to
    the `public` schema (see `app.db.tenancy.get_public_db`)."""
    slug = slug.strip().lower()
    if not _SLUG_PATTERN.match(slug):
        raise InvalidSlugError(
            f"Invalid slug {slug!r}: only lowercase letters, digits, and hyphens are allowed."
        )
    schema_name = _slugify_schema(slug)

    conflict = (
        db.query(Institution)
        .filter((Institution.slug == slug) | (Institution.schema_name == schema_name))
        .one_or_none()
    )
    if conflict is not None:
        raise TenantAlreadyExistsError(f"An institution with slug {slug!r} already exists.")

    institution = Institution(
        name=name,
        code=code,
        slug=slug,
        schema_name=schema_name,
        status="trial",
        subscription_plan=subscription_plan,
        contact_email=contact_email,
        timezone=timezone,
    )
    db.add(institution)
    db.commit()
    # No db.refresh() here: SQLAlchemy 2.x's psycopg dialect populates
    # server-generated columns (created_at/updated_at) via implicit RETURNING
    # at commit time, and the sessionmaker uses expire_on_commit=False (see
    # app/db/session.py), so `institution`'s attributes are already current.
    # A refresh would issue a fresh SELECT that starts a *new* transaction on
    # this caller-supplied session and leaves it open (nothing later on this
    # code path commits/rolls back it back) — which, since tenant tables hold
    # a cross-schema FK to this row (docs/adr/0001-schema-per-tenant.md),
    # can deadlock a later `DROP SCHEMA ... CASCADE` on the same connection
    # (dropping a table's FK constraint takes AccessExclusiveLock on the
    # referenced table too, and has to wait for this session's lingering
    # AccessShareLock to clear first — which it never does mid-request).

    engine = get_engine()
    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

        run_tenant_migrations(schema_name)

        with session_scope(schema_translate_map={None: schema_name}) as tenant_db:
            permission_map = seed_default_permissions(tenant_db)
            seed_default_roles(tenant_db, permission_map)
            seed_default_assessment_types(tenant_db)
            seed_default_course_file_types(tenant_db)
            seed_default_bloom_levels(tenant_db)
            seed_default_mapping_scale(tenant_db)
            if seed_demo:
                seed_demo_data(tenant_db, institution_id=institution.id)

    except Exception as exc:
        logger.exception("tenancy.provisioning_failed", extra={"slug": slug})
        _cleanup_failed_provisioning(db, institution.id, schema_name)
        raise TenantProvisioningError(
            f"Provisioning institution {slug!r} failed: {exc}"
        ) from exc

    logger.info("tenancy.provisioned", extra={"slug": slug, "schema_name": schema_name})
    return institution


def _cleanup_failed_provisioning(db: Session, institution_id: uuid.UUID, schema_name: str) -> None:
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

    institution = db.get(Institution, institution_id)
    if institution is not None:
        db.delete(institution)
        db.commit()
