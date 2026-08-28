"""`get_db` FastAPI dependency: yields a tenant-scoped SQLAlchemy session.

Reads the schema name resolved by `app.middleware.tenancy.TenancyMiddleware`
off `request.state.schema_name` and binds the session to that schema via
`execution_options(schema_translate_map={None: schema_name})`, per
ARCHITECTURE.md §2. Every ORM model is written with no hardcoded schema, so
the same model classes transparently read/write whichever tenant schema this
request was bound to.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.session import get_engine, get_sessionmaker


def program_schema_name(institution_schema: str, program_code: str) -> str:
    """The one place a program's physical schema name is derived from its
    `Program.code` — every call site MUST go through this, not build the
    string inline: `Program.code` is stored as-entered (e.g. "BSCSE"), but
    `app.services.tenancy.provision_program_schema` lowercases it before
    using it as a real schema identifier (Postgres identifier convention,
    same reasoning as institution slugs — see `_SLUG_PATTERN` there).
    Skipping the lowercase here produced a real bug: every one of this
    function's callers previously built `f"{institution_schema}__{code}"`
    directly, silently querying a schema (`..._BSCSE`) that never existed
    (the real one is `..._bscse`) until this was consolidated.
    """
    return f"{institution_schema}__{program_code.lower()}"


def get_db(request: Request) -> Generator[Session]:
    """Per-request tenant-scoped session. Requires TenancyMiddleware to have
    already set `request.state.schema_name` (404s happen in the middleware
    before this dependency is ever reached)."""
    schema_name: str = request.state.schema_name
    SessionLocal = get_sessionmaker()
    connectable = get_engine().execution_options(schema_translate_map={None: schema_name})
    session = SessionLocal(bind=connectable)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_program_db(request: Request, program_code: str) -> Generator[Session]:
    """Session bound to BOTH the institution schema (`None` translate-map key)
    and one program's schema (`"program"` key) simultaneously, per
    docs/adr/0003-schema-per-program.md — institution-shared tables (courses,
    users, org structure) and this program's tables (program_versions, peos,
    program_outcomes, course_offerings, ...) are both reachable in the same
    query, e.g. a `course_offerings` (program schema) join to
    `course_versions` (institution schema).

    Not a FastAPI dependency itself (takes `program_code` as a plain arg,
    not `Depends(...)`) — callers must first resolve and authorize the
    program via `app.services.rbac.get_program_context`, which validates the
    `X-Program-Code` header against the caller's grants before this session
    is ever opened. See `app.services.rbac.get_program_scoped_db`.
    """
    schema_name: str = request.state.schema_name
    program_schema = program_schema_name(schema_name, program_code)
    SessionLocal = get_sessionmaker()
    connectable = get_engine().execution_options(
        schema_translate_map={None: schema_name, "program": program_schema}
    )
    session = SessionLocal(bind=connectable)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_public_db() -> Generator[Session]:
    """Session bound to the `public` schema only (no tenant translation) —
    used by platform-admin-only endpoints (e.g. institution provisioning)."""
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
