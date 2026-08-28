"""Raw-data console: generic table browser/editor (app/services/raw_data.py
has the full design rationale and scoping rules — read it first).

Every endpoint here requires `require_any_grant(*_ANY_RAW_DATA_CODE)` first
(the user holds *some* raw_data.* grant at all), then does its own
finer-grained per-table/per-row resolution via app.services.raw_data —
`require_permission`'s strict scope-matching doesn't fit this module, see
`require_any_grant`'s docstring in app/services/rbac.py.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_engine, get_sessionmaker, session_scope
from app.db.tenancy import get_db, program_schema_name
from app.middleware.audit import get_request_context
from app.models.public.institution import Institution
from app.models.tenant.identity import User
from app.models.tenant.org import Program
from app.models.tenant.raw_data import RawDataChangeRequest
from app.schemas.raw_data import (
    ChangeRequestRead,
    ChangeRequestReview,
    ColumnSchema,
    InstitutionOption,
    RowMutationResult,
    RowsPage,
    TableSchema,
)
from app.services import raw_data as rd
from app.services.audit import write_audit_log
from app.services.rbac import get_user_permission_grants, require_any_grant

logger = logging.getLogger(__name__)

router = APIRouter()

_ANY_RAW_DATA_CODE = (
    "raw_data.manage_all",
    "raw_data.manage_institution",
    "raw_data.manage_scoped",
    "raw_data.propose_scoped",
)


@router.get("/institutions", response_model=list[InstitutionOption])
def list_institutions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant("raw_data.manage_all")),
) -> list[Institution]:
    """Super Administrator only — the cross-institution switcher. Uses a
    fresh unscoped session (public schema), not the tenant-bound `db` this
    endpoint's own permission check ran against."""
    del current_user  # only needed for the permission gate above
    with session_scope() as public_db:
        return public_db.query(Institution).order_by(Institution.slug).all()


def _resolve_institution_schema(
    request: Request, current_user: User, db: Session, institution_slug: str | None
) -> tuple[str, bool]:
    """Resolve which tenant SCHEMA NAME this request actually operates
    against — same institution as the caller logged into (the common case)
    returns the request's own schema; a *different* institution is Super
    Administrator (raw_data.manage_all) only. Returns
    (schema_name, is_cross_institution) — the latter matters for audit
    logging, see `_resolve_target`'s callers below: writing to another
    institution's audit_logs with *this* user's id would violate that
    schema's users FK (the user doesn't exist there), so cross-institution
    actions are logged to the structured app logger instead.
    """
    home_slug = getattr(request.state, "institution_slug", None)
    if not institution_slug or institution_slug == home_slug:
        return request.state.schema_name, False

    grants = get_user_permission_grants(db, current_user.id)
    if not any(code == "raw_data.manage_all" for code, _st, _sid in grants):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a Super Administrator may access a different institution's data.",
        )

    with session_scope() as public_db:
        institution = (
            public_db.query(Institution).filter(Institution.slug == institution_slug).one_or_none()
        )
    if institution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    return institution.schema_name, True


def _resolve_program(
    institution_schema: str,
    is_cross_institution: bool,
    db: Session,
    grants: list[rd.ScopedGrant],
    program_code: str | None,
) -> Program | None:
    """`rd.resolve_active_program` needs a session bound to the TARGET
    institution's schema (the `None` key) — the request's own `db` already
    is that, unless we're crossing institutions, in which case a throwaway
    institution-only session is opened just for this lookup."""
    if not is_cross_institution:
        try:
            return rd.resolve_active_program(db, grants, program_code)
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    SessionLocal = get_sessionmaker()
    inst_only_db = SessionLocal(
        bind=get_engine().execution_options(schema_translate_map={None: institution_schema})
    )
    try:
        return rd.resolve_active_program(inst_only_db, grants, program_code)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    finally:
        inst_only_db.close()


def _resolve_target(
    request: Request,
    current_user: User,
    db: Session,
    grants: list[rd.ScopedGrant],
    institution_slug: str | None,
    program_code: str | None,
) -> tuple[Session, bool, bool, Program | None]:
    """Resolve which schema(s) this request actually operates against.
    Returns (session, is_cross_institution, is_new_session, active_program).

    `is_cross_institution` (audit-logging: tenant `audit_logs` vs the
    structured app logger — see `_resolve_institution_schema`) and
    `is_new_session` (session-lifecycle: whether the caller must
    `commit()`/`close()` it, vs FastAPI's `get_db` already owning that for
    the request's own `db`) are DIFFERENT questions now: resolving a
    program requires a freshly-opened session (its schema_translate_map
    needs a "program" key `db` was never built with — see
    `app.services.rbac.get_program_scoped_db`) even when staying in the
    caller's own institution, so `is_new_session` can be true while
    `is_cross_institution` is false.
    """
    institution_schema, is_cross = _resolve_institution_schema(
        request, current_user, db, institution_slug
    )
    active_program = _resolve_program(institution_schema, is_cross, db, grants, program_code)

    if not is_cross and active_program is None:
        return db, False, False, None

    translate_map: dict[str | None, str] = {None: institution_schema}
    if active_program is not None:
        translate_map["program"] = program_schema_name(institution_schema, active_program.code)

    SessionLocal = get_sessionmaker()
    connectable = get_engine().execution_options(schema_translate_map=translate_map)
    target_db = SessionLocal(bind=connectable)
    return target_db, is_cross, True, active_program


def _grants(db: Session, current_user: User) -> list[rd.ScopedGrant]:
    all_grants = get_user_permission_grants(db, current_user.id)
    return rd.raw_data_grants(all_grants)


def _get_table_or_404(
    table_name: str, *, allow_public: bool, allow_program: bool = False
) -> sa.Table:
    try:
        return rd.get_table(table_name, allow_public=allow_public, allow_program=allow_program)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


def _ensure_table_visible(grants: list[rd.ScopedGrant], table_name: str) -> None:
    if table_name not in rd.accessible_table_names(grants):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have access to table {table_name!r}.",
        )


def _log_mutation(
    *,
    home_db: Session,
    target_db: Session,
    is_cross_institution: bool,
    current_user: User,
    request: Request,
    action: str,
    table_name: str,
    row_pk: str | None,
    previous_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
) -> None:
    if is_cross_institution:
        # Writing to another institution's audit_logs would violate its
        # users FK (this user doesn't exist in that schema) — log to the
        # structured app logger instead, same spirit as tenant provisioning.
        logger.info(
            "raw_data.cross_institution_mutation",
            extra={
                "actor_user_id": str(current_user.id),
                "action": action,
                "table_name": table_name,
                "row_pk": row_pk,
            },
        )
        return
    write_audit_log(
        target_db,
        user_id=current_user.id,
        action=action,
        entity_type=table_name,
        entity_id=None,
        previous_value=previous_value,
        new_value=new_value,
        **get_request_context(request),
    )
    del home_db  # kept in the signature for symmetry/clarity, unused here


@router.get("/tables", response_model=list[str])
def list_tables(
    request: Request,
    institution_slug: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant(*_ANY_RAW_DATA_CODE)),
) -> list[str]:
    grants = _grants(db, current_user)  # permission grants always come from the home tenant
    _institution_schema, is_cross = _resolve_institution_schema(
        request, current_user, db, institution_slug
    )
    if is_cross:
        # Cross-institution access is Super Admin only (enforced in
        # _resolve_institution_schema) — that grant already implies "every
        # table". Pure name-listing, no session needed for either branch.
        names = rd.accessible_table_names(
            [g for g in grants if g.permission_code == "raw_data.manage_all"]
        )
    else:
        names = rd.accessible_table_names(grants)
    return sorted(names)


@router.get("/tables/{table_name}/schema", response_model=TableSchema)
def get_table_schema(
    table_name: str,
    request: Request,
    institution_slug: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant(*_ANY_RAW_DATA_CODE)),
) -> TableSchema:
    del request  # unused: schema introspection never opens a schema-bound session
    grants = _grants(db, current_user)
    allow_public = rd.has_cross_institution_access(grants)
    # allow_program=True unconditionally: this only introspects the Table
    # object's Python-side column metadata, never compiles/executes a query
    # against it, so the "no program schema_translate_map key active" risk
    # get_table's allow_program gate exists for doesn't apply here.
    table = _get_table_or_404(table_name, allow_public=allow_public, allow_program=True)
    _ensure_table_visible(grants, table_name)

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
    request: Request,
    institution_slug: str | None = Query(default=None),
    program_code: str | None = Query(
        default=None,
        description=(
            "Required for a PROGRAM_SCHEMA_TABLES table unless the caller "
            "holds a program-scoped grant (Program Administrator/Coordinator), "
            "which auto-resolves their own program."
        ),
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant(*_ANY_RAW_DATA_CODE)),
) -> RowsPage:
    grants = _grants(db, current_user)
    target_db, is_cross, is_new_session, active_program = _resolve_target(
        request, current_user, db, grants, institution_slug, program_code
    )
    try:
        allow_public = rd.has_cross_institution_access(grants)
        table = _get_table_or_404(
            table_name, allow_public=allow_public, allow_program=active_program is not None
        )
        _ensure_table_visible(grants, table_name)

        row_filter = None if is_cross else rd.build_scope_filter(target_db, table, grants)
        base = sa.select(table)
        count_stmt = sa.select(sa.func.count()).select_from(table)
        if row_filter is not None:
            base = base.where(row_filter)
            count_stmt = count_stmt.where(row_filter)

        total = target_db.execute(count_stmt).scalar_one()
        rows = target_db.execute(base.limit(page_size).offset((page - 1) * page_size)).all()
        return RowsPage(
            rows=[rd.serialize_row(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )
    finally:
        if is_new_session:
            target_db.close()


def _write_mode_for(grants: list[rd.ScopedGrant], is_cross: bool, table_name: str) -> str:
    if is_cross:
        return "immediate"  # already gated to raw_data.manage_all in _resolve_institution_schema
    return rd.resolve_write_mode(grants, table_name)


@router.post(
    "/tables/{table_name}/rows",
    response_model=RowMutationResult,
    status_code=status.HTTP_201_CREATED,
)
def insert_row(
    table_name: str,
    payload: dict[str, Any],
    request: Request,
    institution_slug: str | None = Query(default=None),
    program_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant(*_ANY_RAW_DATA_CODE)),
) -> RowMutationResult:
    grants = _grants(db, current_user)
    target_db, is_cross, is_new_session, active_program = _resolve_target(
        request, current_user, db, grants, institution_slug, program_code
    )
    try:
        allow_public = rd.has_cross_institution_access(grants)
        table = _get_table_or_404(
            table_name, allow_public=allow_public, allow_program=active_program is not None
        )
        _ensure_table_visible(grants, table_name)
        mode = _write_mode_for(grants, is_cross, table_name)
        if mode == "denied":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot write to table {table_name!r}.",
            )

        if mode == "propose":
            scope = rd.resolve_scope_for_write(target_db, grants, table_name)
            if scope is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No applicable program/course scope for this proposal.",
                )
            scope_type, scope_id = scope
            change = RawDataChangeRequest(
                requested_by=current_user.id,
                table_name=table_name,
                operation="insert",
                row_pk=None,
                payload_json=payload,
                previous_json=None,
                status="pending",
                scope_type=scope_type,
                scope_id=scope_id,
            )
            target_db.add(change)
            target_db.flush()
            return RowMutationResult(mode="propose", change_request_id=change.id)

        coerced = {
            col.name: rd.coerce_input_value(col, payload[col.name])
            for col in table.columns
            if col.name in payload
        }
        result = target_db.execute(sa.insert(table).values(**coerced).returning(table))
        row = result.one()
        target_db.flush()
        row_dict = rd.serialize_row(row)
        _log_mutation(
            home_db=db,
            target_db=target_db,
            is_cross_institution=is_cross,
            current_user=current_user,
            request=request,
            action="raw_data.row_inserted",
            table_name=table_name,
            row_pk=str(row_dict.get(rd.primary_key_column(table).name)),
            previous_value=None,
            new_value=row_dict,
        )
        return RowMutationResult(mode="immediate", row=row_dict)
    finally:
        if is_new_session:
            target_db.commit()
            target_db.close()


@router.patch("/tables/{table_name}/rows/{pk}", response_model=RowMutationResult)
def update_row(
    table_name: str,
    pk: str,
    payload: dict[str, Any],
    request: Request,
    institution_slug: str | None = Query(default=None),
    program_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant(*_ANY_RAW_DATA_CODE)),
) -> RowMutationResult:
    grants = _grants(db, current_user)
    target_db, is_cross, is_new_session, active_program = _resolve_target(
        request, current_user, db, grants, institution_slug, program_code
    )
    try:
        allow_public = rd.has_cross_institution_access(grants)
        table = _get_table_or_404(
            table_name, allow_public=allow_public, allow_program=active_program is not None
        )
        _ensure_table_visible(grants, table_name)
        mode = _write_mode_for(grants, is_cross, table_name)
        if mode == "denied":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot write to table {table_name!r}.",
            )

        pk_col = rd.primary_key_column(table)
        pk_value = rd.coerce_input_value(pk_col, pk)
        existing = target_db.execute(sa.select(table).where(pk_col == pk_value)).one_or_none()
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")
        if not is_cross:
            row_filter = rd.build_scope_filter(target_db, table, grants)
            if row_filter is not None:
                in_scope = target_db.execute(
                    sa.select(sa.literal(True))
                    .select_from(table)
                    .where(pk_col == pk_value, row_filter)
                ).one_or_none()
                if in_scope is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="This row is outside your scope.",
                    )
        previous = rd.serialize_row(existing)

        payload = {k: v for k, v in payload.items() if k != pk_col.name}  # PK is never editable

        if mode == "propose":
            scope = rd.resolve_scope_for_write(target_db, grants, table_name)
            if scope is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No applicable program/course scope for this proposal.",
                )
            scope_type, scope_id = scope
            change = RawDataChangeRequest(
                requested_by=current_user.id,
                table_name=table_name,
                operation="update",
                row_pk=pk,
                payload_json=payload,
                previous_json=previous,
                status="pending",
                scope_type=scope_type,
                scope_id=scope_id,
            )
            target_db.add(change)
            target_db.flush()
            return RowMutationResult(mode="propose", change_request_id=change.id)

        coerced = {
            col.name: rd.coerce_input_value(col, payload[col.name])
            for col in table.columns
            if col.name in payload
        }
        result = target_db.execute(
            sa.update(table).where(pk_col == pk_value).values(**coerced).returning(table)
        )
        row = result.one()
        target_db.flush()
        row_dict = rd.serialize_row(row)
        _log_mutation(
            home_db=db,
            target_db=target_db,
            is_cross_institution=is_cross,
            current_user=current_user,
            request=request,
            action="raw_data.row_updated",
            table_name=table_name,
            row_pk=pk,
            previous_value=previous,
            new_value=row_dict,
        )
        return RowMutationResult(mode="immediate", row=row_dict)
    finally:
        if is_new_session:
            target_db.commit()
            target_db.close()


@router.delete("/tables/{table_name}/rows/{pk}", response_model=RowMutationResult)
def delete_row(
    table_name: str,
    pk: str,
    request: Request,
    institution_slug: str | None = Query(default=None),
    program_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant(*_ANY_RAW_DATA_CODE)),
) -> RowMutationResult:
    grants = _grants(db, current_user)
    target_db, is_cross, is_new_session, active_program = _resolve_target(
        request, current_user, db, grants, institution_slug, program_code
    )
    try:
        allow_public = rd.has_cross_institution_access(grants)
        table = _get_table_or_404(
            table_name, allow_public=allow_public, allow_program=active_program is not None
        )
        _ensure_table_visible(grants, table_name)
        mode = _write_mode_for(grants, is_cross, table_name)
        if mode == "denied":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You cannot write to table {table_name!r}.",
            )

        pk_col = rd.primary_key_column(table)
        pk_value = rd.coerce_input_value(pk_col, pk)
        existing = target_db.execute(sa.select(table).where(pk_col == pk_value)).one_or_none()
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Row not found")
        if not is_cross:
            row_filter = rd.build_scope_filter(target_db, table, grants)
            if row_filter is not None:
                in_scope = target_db.execute(
                    sa.select(sa.literal(True))
                    .select_from(table)
                    .where(pk_col == pk_value, row_filter)
                ).one_or_none()
                if in_scope is None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="This row is outside your scope.",
                    )
        previous = rd.serialize_row(existing)

        if mode == "propose":
            scope = rd.resolve_scope_for_write(target_db, grants, table_name)
            if scope is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No applicable program/course scope for this proposal.",
                )
            scope_type, scope_id = scope
            change = RawDataChangeRequest(
                requested_by=current_user.id,
                table_name=table_name,
                operation="delete",
                row_pk=pk,
                payload_json=None,
                previous_json=previous,
                status="pending",
                scope_type=scope_type,
                scope_id=scope_id,
            )
            target_db.add(change)
            target_db.flush()
            return RowMutationResult(mode="propose", change_request_id=change.id)

        target_db.execute(sa.delete(table).where(pk_col == pk_value))
        target_db.flush()
        _log_mutation(
            home_db=db,
            target_db=target_db,
            is_cross_institution=is_cross,
            current_user=current_user,
            request=request,
            action="raw_data.row_deleted",
            table_name=table_name,
            row_pk=pk,
            previous_value=previous,
            new_value=None,
        )
        return RowMutationResult(mode="immediate", row=None)
    finally:
        if is_new_session:
            target_db.commit()
            target_db.close()


# --- Pending change requests (Program Administrator review queue) ----------


def _programs_administered(db: Session, current_user: User) -> set[uuid.UUID]:
    grants = get_user_permission_grants(db, current_user.id)
    return {
        scope_id
        for code, scope_type, scope_id in grants
        if code == "raw_data.approve" and scope_type == "program" and scope_id is not None
    }


@router.get("/pending-changes", response_model=list[ChangeRequestRead])
def list_pending_changes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant("raw_data.approve")),
) -> list[RawDataChangeRequest]:
    program_ids = _programs_administered(db, current_user)
    if not program_ids:
        return []
    return (
        db.query(RawDataChangeRequest)
        .filter(
            RawDataChangeRequest.scope_type == "program",
            RawDataChangeRequest.scope_id.in_(program_ids),
        )
        .order_by(RawDataChangeRequest.created_at.desc())
        .all()
    )


def _get_reviewable_request(
    db: Session, current_user: User, change_id: uuid.UUID
) -> RawDataChangeRequest:
    change = db.get(RawDataChangeRequest, change_id)
    if change is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Change request not found"
        )
    if change.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Change request is already {change.status!r}.",
        )
    program_ids = _programs_administered(db, current_user)
    if change.scope_type != "program" or change.scope_id not in program_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This change request is outside a program you administer.",
        )
    return change


@router.post("/pending-changes/{change_id}/approve", response_model=ChangeRequestRead)
def approve_pending_change(
    change_id: uuid.UUID,
    payload: ChangeRequestReview,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant("raw_data.approve")),
) -> RawDataChangeRequest:
    change = _get_reviewable_request(db, current_user, change_id)
    # `_get_reviewable_request` already confirmed change.scope_type ==
    # "program" and change.scope_id is a program this approver administers
    # — if the change's table is a PROGRAM_SCHEMA_TABLES member, applying it
    # needs a session bound to that specific program's schema (`db` only
    # has the institution schema); resolved directly from the change's own
    # scope_id rather than re-deriving it, since it's already validated.
    is_program_table = change.table_name in rd.PROGRAM_SCHEMA_TABLES
    apply_db = db
    if is_program_table:
        program = db.get(Program, change.scope_id)
        if program is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Program no longer exists"
            )
        institution_schema: str = request.state.schema_name
        SessionLocal = get_sessionmaker()
        apply_db = SessionLocal(
            bind=get_engine().execution_options(
                schema_translate_map={
                    None: institution_schema,
                    "program": program_schema_name(institution_schema, program.code),
                }
            )
        )

    try:
        table = _get_table_or_404(change.table_name, allow_public=False, allow_program=True)
        pk_col = rd.primary_key_column(table)

        if change.operation == "insert":
            coerced = {
                col.name: rd.coerce_input_value(col, change.payload_json[col.name])
                for col in table.columns
                if change.payload_json and col.name in change.payload_json
            }
            applied_row = apply_db.execute(
                sa.insert(table).values(**coerced).returning(table)
            ).one()
        else:
            pk_value = rd.coerce_input_value(pk_col, change.row_pk)
            if change.operation == "update":
                coerced = {
                    col.name: rd.coerce_input_value(col, change.payload_json[col.name])
                    for col in table.columns
                    if change.payload_json and col.name in change.payload_json
                }
                applied_row = apply_db.execute(
                    sa.update(table).where(pk_col == pk_value).values(**coerced).returning(table)
                ).one()
            else:  # delete
                apply_db.execute(sa.delete(table).where(pk_col == pk_value))
                applied_row = None

        if is_program_table:
            apply_db.commit()
    finally:
        if is_program_table:
            apply_db.close()

    change.status = "approved"
    change.reviewed_by = current_user.id
    change.review_note = payload.review_note
    change.reviewed_at = datetime.now(UTC)
    db.add(change)
    db.flush()

    write_audit_log(
        db,
        user_id=current_user.id,
        action="raw_data.change_request_approved",
        entity_type=change.table_name,
        entity_id=change.id,
        previous_value=change.previous_json,
        new_value=rd.serialize_row(applied_row) if applied_row is not None else None,
        **get_request_context(request),
    )
    return change


@router.post("/pending-changes/{change_id}/reject", response_model=ChangeRequestRead)
def reject_pending_change(
    change_id: uuid.UUID,
    payload: ChangeRequestReview,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_grant("raw_data.approve")),
) -> RawDataChangeRequest:
    change = _get_reviewable_request(db, current_user, change_id)
    change.status = "rejected"
    change.reviewed_by = current_user.id
    change.review_note = payload.review_note
    change.reviewed_at = datetime.now(UTC)
    db.add(change)
    db.flush()

    write_audit_log(
        db,
        user_id=current_user.id,
        action="raw_data.change_request_rejected",
        entity_type=change.table_name,
        entity_id=change.id,
        previous_value=None,
        new_value={"review_note": payload.review_note},
        **get_request_context(request),
    )
    return change
