"""Alembic environment for the `public`-schema migration chain.

Applied once (not per tenant) — see ARCHITECTURE.md §2. Targets
`PublicBase.metadata` only (`institutions`, `platform_admins`).
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import models so they register on PublicBase.metadata before autogenerate.
import app.models.public  # noqa: F401
from app.core.config import settings
from app.db.base import PublicBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = PublicBase.metadata


def include_object(obj, name, type_, reflected, compare_to) -> bool:  # noqa: ARG001
    """PublicBase and TenantBase share one MetaData (see app/db/base.py), so
    without this filter autogenerate here would also see every tenant table.
    Only tables explicitly in the `public` schema belong to this chain."""
    if type_ == "table":
        return obj.schema == "public"
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url") or settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_object=include_object,
        version_table_schema="public",
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Programmatic callers (scripts, tests) can hand in an already-open
    # connection via config.attributes["connection"]; otherwise build our
    # own engine from settings.database_url.
    connectable = config.attributes.get("connection")

    if connectable is None:
        configuration = config.get_section(config.config_ini_section) or {}
        configuration["sqlalchemy.url"] = settings.database_url
        engine = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
        with engine.connect() as connection:
            _run(connection)
    else:
        _run(connectable)


def _run(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        include_object=include_object,
        version_table_schema="public",
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
