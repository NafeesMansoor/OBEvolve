"""Schemas for the CO-failure continuous-improvement workflow (spec §5,
app.models.tenant.obe.improvement.ImprovementPlan)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# The spec's own enumerated list of intervention types, plus "other" for
# anything else (paired with `proposed_action_detail` for the explanation
# the spec asks "other" to carry).
ProposedAction = Literal[
    "new_assessment",
    "revise_assessment",
    "change_assessment_type",
    "adjust_co_marks",
    "revise_co_wording",
    "new_co",
    "remove_restructure_co",
    "new_topic",
    "revise_topics",
    "change_teaching_methodology",
    "change_marks_distribution",
    "change_assessment_distribution",
    "additional_materials",
    "remedial_activities",
    "revise_content",
    "other",
]

ImprovementPlanStatus = Literal["proposed", "approved", "rejected", "implemented"]


class ImprovementPlanCreate(BaseModel):
    course_section_id: uuid.UUID
    course_outcome_id: uuid.UUID
    problem_observation: str = Field(min_length=1)
    proposed_action: ProposedAction
    proposed_action_detail: str | None = None
    reason: str = Field(min_length=1)
    expected_improvement: str = Field(min_length=1)
    implementation_term_id: uuid.UUID | None = None
    responsible_user_id: uuid.UUID | None = None
    evidence: str | None = None


class ImprovementPlanUpdate(BaseModel):
    """Only while `status == "proposed"` — see endpoints/improvement.py."""

    problem_observation: str = Field(min_length=1)
    proposed_action: ProposedAction
    proposed_action_detail: str | None = None
    reason: str = Field(min_length=1)
    expected_improvement: str = Field(min_length=1)
    implementation_term_id: uuid.UUID | None = None
    responsible_user_id: uuid.UUID | None = None
    evidence: str | None = None


class ImprovementPlanReview(BaseModel):
    approve: bool
    remarks: str | None = None


class ImprovementPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_section_id: uuid.UUID
    course_outcome_id: uuid.UUID
    problem_observation: str
    proposed_action: str
    proposed_action_detail: str | None
    reason: str
    expected_improvement: str
    implementation_term_id: uuid.UUID | None
    responsible_user_id: uuid.UUID | None
    status: str
    evidence: str | None
    created_by: uuid.UUID | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
