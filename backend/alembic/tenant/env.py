"""Alembic environment for the `tenant`-schema migration chain.

Applied once *per tenant schema* (see ARCHITECTURE.md §2 and
`scripts/migrate_all_tenants.py`). The same migration scripts apply
unmodified to every tenant because the target schema is injected via
`execution_options(schema_translate_map={None: schema_name})` rather than
hardcoded into any migration.

The target schema is resolved, in priority order, from:
1. `config.attributes["schema_name"]` — set by programmatic callers
   (`app.services.tenancy.provision_tenant`, `scripts/migrate_all_tenants.py`).
2. `-x schema=tenant_<slug>` on the CLI, e.g.
   `alembic -x schema=tenant_demo upgrade head`.

Each tenant schema gets its own `alembic_version` table (via
`version_table_schema`), so tenants can be migrated independently.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import models so they register on TenantBase.metadata before autogenerate.
import app.models.tenant  # noqa: F401
from app.core.config import settings
from app.db.base import TenantBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = TenantBase.metadata


def include_object(obj, name, type_, reflected, compare_to) -> bool:  # noqa: ARG001
    """PublicBase and TenantBase share one MetaData (see app/db/base.py), so
    without this filter autogenerate here would also see the public-schema
    tables. Tenant tables are declared with no explicit schema (resolved via
    schema_translate_map at runtime), so `schema is None` identifies them."""
    if type_ == "table":
        return obj.schema is None
    return True


def get_schema_name() -> str:
    schema_name = config.attributes.get("schema_name")
    if schema_name:
        return schema_name

    x_args = context.get_x_argument(as_dictionary=True)
    schema_name = x_args.get("schema")
    if schema_name:
        return schema_name

    raise RuntimeError(
        "Tenant schema not specified. Pass -x schema=tenant_<slug> on the CLI, "
        "or set config.attributes['schema_name'] when invoking programmatically."
    )


def run_migrations_offline() -> None:
    schema_name = get_schema_name()
    url = config.get_main_option("sqlalchemy.url") or settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_object=include_object,
        version_table_schema=schema_name,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    schema_name = get_schema_name()
    connectable = config.attributes.get("connection")

    if connectable is None:
        configuration = config.get_section(config.config_ini_section) or {}
        configuration["sqlalchemy.url"] = settings.database_url
        engine = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
        engine = engine.execution_options(schema_translate_map={None: schema_name})
        with engine.connect() as connection:
            _run(connection, schema_name)
    else:
        connection = connectable.execution_options(schema_translate_map={None: schema_name})
        _run(connection, schema_name)


def _run(connection, schema_name: str) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_object=include_object,
        version_table_schema=schema_name,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
