"""Alembic environment for the `program`-schema migration chain.

Applied once *per program schema* (see docs/adr/0003-schema-per-program.md
and `scripts/migrate_all_programs.py`). The same migration scripts apply
unmodified to every program because the target schemas are injected via
`execution_options(schema_translate_map=...)` rather than hardcoded into any
migration — mirrors `alembic/tenant/env.py`, extended to a *second*
translate-map key.

Program-specific models (`app/models/tenant/*`, the ones marked
`__table_args__ = {"schema": "program"}`) share `TenantBase.metadata` with
the institution-shared tenant models, so `target_metadata` here is the same
`TenantBase.metadata` used by the tenant chain — `include_object` is what
narrows autogenerate/version-tracking down to just the schema="program"
subset.

Two schemas must be resolved for every run, not one:
- `institution_schema` (e.g. `tenant_ulab-cse`) — some program-schema tables
  carry a FK into institution-shared tables (`programs`, `academic_years`,
  `users`, `course_versions`, ...) with no explicit schema= override, which
  relies on the `None` translate-map key resolving to this schema.
- `program_schema` (e.g. `tenant_ulab-cse__bscse`) — where these tables
  actually live, and where this chain's own `alembic_version` table is
  tracked (`version_table_schema`).

Both are resolved, in priority order, from:
1. `config.attributes["institution_schema"]` / `config.attributes["program_schema"]`
   — set by programmatic callers (`app.services.tenancy.provision_program_schema`,
   `scripts/migrate_all_programs.py`).
2. `-x institution_schema=... -x program_schema=...` on the CLI, e.g.
   `alembic -x institution_schema=tenant_demo -x program_schema=tenant_demo__bscse upgrade head`.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import models so they register on TenantBase.metadata before autogenerate —
# same shared metadata as the tenant chain (see module docstring).
import app.models.tenant  # noqa: F401
from app.core.config import settings
from app.db.base import TenantBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = TenantBase.metadata


def include_object(obj, name, type_, reflected, compare_to) -> bool:  # noqa: ARG001
    """PublicBase and TenantBase share one MetaData (see app/db/base.py), and
    TenantBase itself mixes institution-shared (schema=None) and
    program-specific (schema="program") tables — without this filter,
    autogenerate here would see all three. Program-specific tables are
    declared with the "program" marker schema (resolved to a real schema via
    schema_translate_map at runtime), so `schema == "program"` identifies
    them."""
    if type_ == "table":
        return obj.schema == "program"
    return True


def _resolve(attr_key: str, x_arg_key: str) -> str:
    value = config.attributes.get(attr_key)
    if value:
        return value

    x_args = context.get_x_argument(as_dictionary=True)
    value = x_args.get(x_arg_key)
    if value:
        return value

    raise RuntimeError(
        f"{x_arg_key} not specified. Pass -x {x_arg_key}=... on the CLI, "
        f"or set config.attributes[{attr_key!r}] when invoking programmatically."
    )


def get_institution_schema() -> str:
    return _resolve("institution_schema", "institution_schema")


def get_program_schema() -> str:
    return _resolve("program_schema", "program_schema")


def run_migrations_offline() -> None:
    program_schema = get_program_schema()
    url = config.get_main_option("sqlalchemy.url") or settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_object=include_object,
        version_table_schema=program_schema,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    institution_schema = get_institution_schema()
    program_schema = get_program_schema()
    connectable = config.attributes.get("connection")

    translate_map = {None: institution_schema, "program": program_schema}

    if connectable is None:
        configuration = config.get_section(config.config_ini_section) or {}
        configuration["sqlalchemy.url"] = settings.database_url
        engine = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
        engine = engine.execution_options(schema_translate_map=translate_map)
        with engine.connect() as connection:
            _run(connection, program_schema)
    else:
        connection = connectable.execution_options(schema_translate_map=translate_map)
        _run(connection, program_schema)


def _run(connection, program_schema: str) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_object=include_object,
        version_table_schema=program_schema,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
