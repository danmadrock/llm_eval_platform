from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from llm_eval_platform.models.evaluation_result import EvaluationResult
from llm_eval_platform.models.run import Run
from llm_eval_platform.models.run_metric import RunMetric


class RunAggregator:
    def update_summary(self, db: Session, run_id: UUID) -> None:
        run = db.scalar(select(Run).where(Run.id == run_id))
        if run is None:
            raise ValueError(f"Run {run_id} was not found.")

        results = db.scalars(
            select(EvaluationResult)
            .where(EvaluationResult.run_id == run_id)
            .order_by(EvaluationResult.example_index)
        ).all()

        score_values = [result.score for result in results if result.score is not None]
        latencies = [
            float(latency)
            for result in results
            if (latency := result.result_metadata.get("latency_ms")) is not None # most effective by walrus
        ]
        costs = [
            float(cost)
            for result in results
            if (
                cost := (
                    result.result_metadata.get("cost_usd")
                    if result.result_metadata.get("cost_usd") is not None
                    else (result.result_metadata.get("metric_scores") or {}).get("cost")
                )
            )
            is not None
        ]

        status_breakdown = dict(Counter(result.status for result in results))

        aggregate_metrics: dict[str, float] = {}
        if score_values:
            aggregate_metrics["average_score"] = mean(score_values)
        if latencies:
            aggregate_metrics["latency_avg_ms"] = mean(latencies)
            aggregate_metrics["latency_p50_ms"] = self._percentile(latencies, 50)
            aggregate_metrics["latency_p95_ms"] = self._percentile(latencies, 95)
        if costs:
            aggregate_metrics["total_cost_usd"] = sum(costs)

        plugin_scores: dict[str, list[float]] = {}
        for result in results:
            metric_scores = result.result_metadata.get("metric_scores") or {}
            for metric_name, score in metric_scores.items():
                plugin_scores.setdefault(str(metric_name), []).append(float(score))

        for metric_name, values in plugin_scores.items():
            if values:
                aggregate_metrics[f"metric.{metric_name}.avg"] = mean(values)

        now = datetime.now(timezone.utc)
        existing_metrics = {
            metric.metric_name: metric
            for metric in db.scalars(select(RunMetric).where(RunMetric.run_id == run_id)).all()
        }
        seen: set[str] = set()
        for metric_name, value in aggregate_metrics.items():
            metric = existing_metrics.get(metric_name)
            if metric is None:
                metric = RunMetric(
                    run_id=run_id,
                    metric_name=metric_name,
                    value=value,
                    computed_at=now,
                )
            else:
                metric.value = value
                metric.computed_at = now
            db.add(metric)
            seen.add(metric_name)

        for metric_name, metric in existing_metrics.items():
            if metric_name not in seen:
                db.delete(metric)

        parameters = dict(run.parameters or {})
        parameters["summary"] = {
            "average_score": aggregate_metrics.get("average_score"),
            "status_breakdown": status_breakdown,
            "metrics": aggregate_metrics,
        }
        run.parameters = parameters
        db.add(run)
        db.flush()

    def get_analytics(self, db: Session, run_id: UUID) -> dict[str, object]:
        run = db.scalar(select(Run).where(Run.id == run_id))
        if run is None:
            raise ValueError(f"Run {run_id} was not found.")

        metric_rows = db.scalars(select(RunMetric).where(RunMetric.run_id == run_id)).all()
        metrics_map = {row.metric_name: row.value for row in metric_rows}
        summary = dict((run.parameters or {}).get("summary") or {})

        return {
            "run_id": run_id,
            "status": run.status,
            "examples": {
                "total": run.total_examples,
                "processed": run.processed_examples,
                "completed": run.completed_examples,
                "failed": run.failed_examples,
            },
            "kpis": {
                "average_score": metrics_map.get("average_score"),
                "latency_p50_ms": metrics_map.get("latency_p50_ms"),
                "latency_p95_ms": metrics_map.get("latency_p95_ms"),
                "latency_avg_ms": metrics_map.get("latency_avg_ms"),
                "total_cost_usd": metrics_map.get("total_cost_usd"),
            },
            "metrics": metrics_map,
            "status_breakdown": summary.get("status_breakdown", {}),
        }
    
    @staticmethod
    def _percentile(values: list[float], percentile: int) -> float:
        if not values:
            raise ValueError("Cannot compute a percentile for an empty list.")
        ordered = sorted(values)
        if len(ordered) == 1:
            return ordered[0]
        rank = (len(ordered) - 1) * (percentile / 100)
        lower = int(rank)
        upper = min(lower + 1, len(ordered) - 1)
        weight = rank - lower
        return ordered[lower] + ((ordered[upper] - ordered[lower]) * weight)