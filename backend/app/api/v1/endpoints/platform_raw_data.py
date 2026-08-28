"""Platform-admin raw-data console: full, unscoped read/write access to
every institution's data — this is what "the platform admin has full
access to all the databases" actually means in this codebase.

Deliberately a separate, much simpler surface than
app/api/v1/endpoints/raw_data.py (the tenant-user console): a platform
admin isn't a member of any institution, so there's no "home" institution,
no row-level scope to compute (raw_data.manage_all's equivalent, always —
see app.services.raw_data.build_scope_filter's own `None` short-circuit for
manage_all/manage_institution), and no propose-mode (nothing to propose
*to* — a platform admin's write is definitionally already the highest
authority). What both surfaces still share: `app.services.raw_data`'s
table registries, column/row (de)serialization, and the "which program
schema" resolution mechanics (docs/adr/0003-schema-per-program.md).

Every mutation is audit-logged to the structured app logger, never a
tenant's own `audit_logs` table — `PlatformAdmin.id` isn't a valid FK
there (same reasoning as the tenant console's cross-institution writes;
see raw_data.py's `_log_mutation`).
"""

from __future__ import annotations

import logging
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.platform_auth import get_current_platform_admin
from app.db.session import get_engine, get_sessionmaker, session_scope
from app.db.tenancy import program_schema_name
from app.models.public.institution import Institution
from app.models.public.platform_admin import PlatformAdmin
from app.models.tenant.org import Program
from app.schemas.raw_data import ColumnSchema, RowMutationResult, RowsPage, TableSchema
from app.services import raw_data as rd

logger = logging.getLogger(__name__)

router = APIRouter()


def _institution_schema(institution_slug: str) -> str:
    with session_scope() as public_db:
        institution = (
            public_db.query(Institution).filter(Institution.slug == institution_slug).one_or_none()
        )
    if institution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    return institution.schema_name


def _open_session(institution_schema: str, program_code: str | None) -> Session:
    """Opens a session bound to the institution schema, plus the program
    schema too if `program_code` is given — validated to actually exist
    first (a quick institution-only lookup), so a bad program_code 404s
    cleanly instead of surfacing as an UndefinedTable error against a
    schema that was never created."""
    translate_map: dict[str | None, str] = {None: institution_schema}
    if program_code is not None:
        with session_scope(schema_translate_map={None: institution_schema}) as check_db:
            program = check_db.query(Program).filter(Program.code == program_code).one_or_none()
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown program {program_code!r}"
            )
        translate_map["program"] = program_schema_name(institution_schema, program_code)
    SessionLocal = get_sessionmaker()
    return SessionLocal(bind=get_engine().execution_options(schema_translate_map=translate_map))


def _get_table_or_404(table_name: str, *, allow_program: bool) -> sa.Table:
    try:
        return rd.get_table(table_name, allow_public=True, allow_program=allow_program)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/tables", response_model=list[str])
def list_tables(
    institution_slug: str = Query(...),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> list[str]:
    # Every institution's tenant schema has an identical table set (the same
    # Alembic chain), so institution_slug doesn't actually change this list
    # — accepted (and validated) anyway for URL/API consistency with every
    # other endpoint here, and so an unknown slug still 404s instead of
    # silently listing tables for a target that doesn't exist.
    _institution_schema(institution_slug)
    return sorted(rd.platform_admin_table_names())


@router.get("/tables/{table_name}/schema", response_model=TableSchema)
def get_table_schema(
    table_name: str,
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> TableSchema:
    # allow_program=True unconditionally: pure Python-side column
    # introspection, never compiles/executes a query — see the identical
    # reasoning in app.api.v1.endpoints.raw_data.get_table_schema.
    table = _get_table_or_404(table_name, allow_program=True)
    columns = [
        ColumnSchema(
            name=col.name,
            type=rd.column_type_tag(col),
            nullable=col.nullable,
            is_primary_key=col.primary_key,
            foreign_key=rd.foreign_key_ref(col),
        )
        for col in table.columns
    ]
    return TableSchema(table_name=table_name, columns=columns)


@router.get("/tables/{table_name}/rows", response_model=RowsPage)
def list_rows(
    table_name: str,
    institution_slug: str = Query(...),
    program_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> RowsPage:
    institution_schema = _institution_schema(institution_slug)
    db = _open_session(institution_schema, program_code)
    try:
        table = _get_table_or_404(table_name, allow_program=program_code is not None)
        total = db.execute(sa.select(sa.func.count()).select_from(table)).scalar_one()
        rows = db.execute(sa.select(table).limit(page_size).offset((page - 1) * page_size)).all()
        return RowsPage(
            rows=[rd.serialize_row(r) for r in rows], total=total, page=page, page_size=page_size
        )
    finally:
        db.close()


def _log_mutation(
    *, admin: PlatformAdmin, action: str, table_name: str, row_pk: str | None
) -> None:
    logger.info(
        "platform_raw_data.mutation",
        extra={
            "actor_admin_id": str(admin.id),
            "action": action,
            "table_name": table_name,
            "row_pk": row_pk,
        },
    )


@router.post(
    "/tables/{table_name}/rows",
    response_model=RowMutationResult,
    status_code=status.HTTP_201_CREATED,
)
def insert_row(
    table_name: str,
    payload: dict[str, Any],
    institution_slug: str = Query(...),
    program_code: str | None = Query(default=None),
    admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> RowMutationResult:
    institution_schema = _institution_schema(institution_slug)
    db = _open_session(institution_schema, program_code)
    try:
        table = _get_table_or_404(table_name, allow_program=program_code is not None)
        coerced = {
            col.name: rd.coerce_input_value(col, payload[col.name])
            for col in table.columns
            if col.name in payload
        }
        row = db.execute(sa.insert(table).values(**coerced).returning(table)).one()
        db.commit()
        row_dict = rd.serialize_row(row)
        _log_mutation(
            admin=admin,
            action="row_inserted",
            table_name=table_name,
            row_pk=str(row_dict.get(rd.primary_key_column(table).name)),
        )
        return RowMutationResult(mode="immediate", row=row_dict)
    finally:
        db.close()


@router.patch("/tables/{table_name}/rows/{pk}", response_model=RowMutationResult)
def update_row(
    table_name: str,
    pk: str,
    payload: dict[str, Any],
    institution_slug: str = Query(...),
    program_code: str | None = Query(default=None),
    admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> RowMutationResult:
    institution_schema = _institution_schema(institution_slug)
    db = _open_session(institution_schema, program_code)
    try:
        table = _get_table_or_404(table_name, allow_program=program_code is not None)
        pk_col = rd.primary_key_column(table)
        pk_value = rd.coerce_input_value(pk_col, pk)
        existing = db.execute(sa.select(table).where(pk_col == pk_value)).one_or_none()
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")

        payload = {k: v for k, v in payload.items() if k != pk_col.name}  # PK is never editable
        coerced = {
            col.name: rd.coerce_input_value(col, payload[col.name])
            for col in table.columns
            if col.name in payload
        }
        row = db.execute(
            sa.update(table).where(pk_col == pk_value).values(**coerced).returning(table)
        ).one()
        db.commit()
        row_dict = rd.serialize_row(row)
        _log_mutation(admin=admin, action="row_updated", table_name=table_name, row_pk=pk)
        return RowMutationResult(mode="immediate", row=row_dict)
    finally:
        db.close()


@router.delete("/tables/{table_name}/rows/{pk}", response_model=RowMutationResult)
def delete_row(
    table_name: str,
    pk: str,
    institution_slug: str = Query(...),
    program_code: str | None = Query(default=None),
    admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> RowMutationResult:
    institution_schema = _institution_schema(institution_slug)
    db = _open_session(institution_schema, program_code)
    try:
        table = _get_table_or_404(table_name, allow_program=program_code is not None)
        pk_col = rd.primary_key_column(table)
        pk_value = rd.coerce_input_value(pk_col, pk)
        existing = db.execute(sa.select(table).where(pk_col == pk_value)).one_or_none()
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")

        db.execute(sa.delete(table).where(pk_col == pk_value))
        db.commit()
        _log_mutation(admin=admin, action="row_deleted", table_name=table_name, row_pk=pk)
        return RowMutationResult(mode="immediate", row=None)
    finally:
        db.close()
