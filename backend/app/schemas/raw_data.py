"""Schemas for the raw-data console (app/api/v1/endpoints/raw_data.py)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class InstitutionOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    schema_name: str


class ColumnSchema(BaseModel):
    name: str
    type: str
    nullable: bool
    is_primary_key: bool
    foreign_key: str | None


class TableSchema(BaseModel):
    table_name: str
    columns: list[ColumnSchema]


class RowsPage(BaseModel):
    rows: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class RowMutationResult(BaseModel):
    """Returned by POST/PATCH/DELETE on a row — either the applied row
    (`mode="immediate"`) or the pending request that was created instead
    (`mode="propose"`)."""

    mode: str  # "immediate" | "propose"
    row: dict[str, Any] | None = None
    change_request_id: uuid.UUID | None = None


class ChangeRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requested_by: uuid.UUID
    table_name: str
    operation: str
    row_pk: str | None
    payload_json: dict[str, Any] | None
    previous_json: dict[str, Any] | None
    status: str
    scope_type: str
    scope_id: uuid.UUID
    reviewed_by: uuid.UUID | None
    review_note: str | None
    created_at: datetime
    reviewed_at: datetime | None


class ChangeRequestReview(BaseModel):
    review_note: str | None = None
