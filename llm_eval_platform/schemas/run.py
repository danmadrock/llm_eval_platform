from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RunMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    metric_name: str
    value: float
    computed_at: datetime
    created_at: datetime
    updated_at: datetime


class RunCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    experiment_id: UUID
    dataset_version_id: UUID
    prompt_version_id: UUID
    model_config_id: UUID
    baseline_run_id: UUID | None = None
    status: str = Field(default="created", min_length=1, max_length=50)
    parameters: dict = Field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str | None = Field(default=None, min_length=1, max_length=50)
    total_examples: int | None = Field(default=None, ge=0)
    processed_examples: int | None = Field(default=None, ge=0)
    completed_examples: int | None = Field(default=None, ge=0)
    failed_examples: int | None = Field(default=None, ge=0)
    parameters: dict | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result_artifact_uri: str | None = None
    regression_status: str | None = None
    regression_summary: dict | None = None


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    experiment_id: UUID
    dataset_version_id: UUID
    prompt_version_id: UUID
    model_config_id: UUID
    baseline_run_id: UUID | None

    status: str
    parameters: dict
    total_examples: int
    processed_examples: int
    completed_examples: int
    failed_examples: int
    result_artifact_uri: str | None
    regression_status: str | None
    regression_summary: dict
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    metrics: list[RunMetricRead] = Field(default_factory=list)


class RunAnalyticsRead(BaseModel):
    run_id: UUID
    status: str
    examples: dict[str, int]
    kpis: dict[str, float | None]
    metrics: dict[str, float]
    status_breakdown: dict[str, int]


class RegressionReportRead(BaseModel):
    candidate_run_id: UUID
    baseline_run_id: UUID
    status: str
    score_delta: float | None
    failure_rate_delta: float | None
    policy_thresholds: dict[str, float]
    reasons: list[str] = Field(default_factory=list)