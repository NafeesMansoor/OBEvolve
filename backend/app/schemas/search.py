"""Schemas for the lightweight cross-entity global search
(app/api/v1/endpoints/search.py)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

SearchResultType = Literal[
    "course",
    "student",
    "faculty",
    "assessment",
    "program_outcome",
    "course_outcome",
    "program",
]


class SearchResultItem(BaseModel):
    type: SearchResultType
    id: str
    title: str
    subtitle: str | None
    url_hint: str


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
