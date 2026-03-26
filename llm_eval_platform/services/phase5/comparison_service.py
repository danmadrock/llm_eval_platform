from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from llm_eval_platform.models.run import Run


@dataclass
class FrontierPoint:
    run_id: UUID
    experiment_id: UUID
    created_at: datetime
    quality_score: float | None
    total_cost_usd: float | None
    latency_p95_ms: float | None
    status: str
    pareto_optimal: bool = False


class ComparisonService:
    """Experiment-level comparison helpers for Phase 5 differentiation APIs."""

    def get_quality_cost_frontier(self, db: Session, experiment_id: UUID) -> dict[str, object]:
        stmt = (
            select(Run)
            .options(selectinload(Run.metrics))
            .where(Run.experiment_id == experiment_id)
            .order_by(Run.created_at.desc())
        )
        tenant_id = db.info.get("tenant_id")
        if tenant_id:
            stmt = stmt.where(Run.tenant_id == tenant_id)
        runs = db.scalars(stmt).all()

        points: list[FrontierPoint] = []
        for run in runs:
            metrics = {metric.metric_name: metric.value for metric in run.metrics}
            points.append(
                FrontierPoint(
                    run_id=run.id,
                    experiment_id=run.experiment_id,
                    created_at=run.created_at,
                    quality_score=self._optional_float(metrics.get("average_score")),
                    total_cost_usd=self._optional_float(metrics.get("total_cost_usd")),
                    latency_p95_ms=self._optional_float(metrics.get("latency_p95_ms")),
                    status=run.status,
                )
            )

        frontier_ids = self._pareto_frontier(points)
        for point in points:
            point.pareto_optimal = point.run_id in frontier_ids

        return {
            "experiment_id": experiment_id,
            "objective": "maximize_quality_minimize_cost",
            "total_runs": len(runs),
            "compared_runs": len(
                [point for point in points if point.quality_score is not None and point.total_cost_usd is not None]
            ),
            "points": [
                {
                    "run_id": point.run_id,
                    "experiment_id": point.experiment_id,
                    "created_at": point.created_at,
                    "quality_score": point.quality_score,
                    "total_cost_usd": point.total_cost_usd,
                    "latency_p95_ms": point.latency_p95_ms,
                    "status": point.status,
                    "pareto_optimal": point.pareto_optimal,
                }
                for point in points
            ],
        }

    @staticmethod
    def _pareto_frontier(points: list[FrontierPoint]) -> set[UUID]:
        eligible = [
            point for point in points if point.quality_score is not None and point.total_cost_usd is not None
        ]
        frontier: set[UUID] = set()

        for candidate in eligible:
            candidate_quality = candidate.quality_score
            candidate_cost = candidate.total_cost_usd
            if candidate_quality is None or candidate_cost is None:
                continue
            dominated = False
            for peer in eligible:
                if peer.run_id == candidate.run_id:
                    continue
                peer_quality = peer.quality_score
                peer_cost = peer.total_cost_usd
                if peer_quality is None or peer_cost is None:
                    continue
                if (
                    peer_quality >= candidate_quality
                    and peer_cost <= candidate_cost
                    and (peer_quality > candidate_quality or peer_cost < candidate_cost)
                ):
                    dominated = True
                    break
            if not dominated:
                frontier.add(candidate.run_id)
        return frontier

    @staticmethod
    def _optional_float(value: object) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float, str)):
            return float(value)
        return None
