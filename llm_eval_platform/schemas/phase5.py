from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class OptimizationHookRead(BaseModel):
    run_id: UUID
    experiment_id: UUID
    hook_type: str
    metrics: dict[str, float | None]
    failure_rate: float
    suggested_actions: list[str]
    context: dict[str, UUID]


class HumanReviewClaimRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=128)


class HumanReviewSubmitRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=128)
    decision: str = Field(pattern="^(approved|rejected)$")
    notes: str | None = None
    score_override: float | None = None
