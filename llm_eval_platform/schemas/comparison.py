from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FrontierPointRead(BaseModel):
    run_id: UUID
    experiment_id: UUID
    created_at: datetime
    quality_score: float | None
    total_cost_usd: float | None
    latency_p95_ms: float | None
    status: str
    pareto_optimal: bool


class QualityCostFrontierRead(BaseModel):
    experiment_id: UUID
    objective: str
    total_runs: int
    compared_runs: int
    points: list[FrontierPointRead]
