from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy.orm import Session

from llm_eval_platform.services.runs.run_service import RunService


class PromptOptimizationHookService:
    def __init__(
        self,
        run_service: RunService | None = None,
    ) -> None:
        self.run_service = run_service or RunService()

    def build_hook_payload(self, db: Session, run_id: UUID) -> dict[str, object]:
        run = self.run_service.get(db, run_id)
        analytics = self.run_service.get_analytics(db, run_id)

        kpis = self._to_mapping(analytics.get("kpis"))
        examples = self._to_mapping(analytics.get("examples"))

        hints: list[str] = []
        avg_score = self._optional_float(kpis.get("average_score"))
        failure_rate = self._failure_rate(examples)
        p95_latency = self._optional_float(kpis.get("latency_p95_ms"))

        if avg_score is not None and avg_score < 0.75:
            hints.append("Improve instruction clarity and add few-shot demonstrations.")
        if failure_rate > 0.1:
            hints.append("Add guardrails for invalid output schema and refusal handling.")
        if p95_latency is not None and p95_latency > 3000:
            hints.append("Reduce prompt verbosity or lower max_tokens to improve tail latency.")
        if not hints:
            hints.append("No critical issues detected; run A/B prompt variants for incremental gains.")

        payload = {
            "run_id": run.id,
            "experiment_id": run.experiment_id,
            "hook_type": "prompt_optimization_signal",
            "metrics": {
                "average_score": avg_score,
                "latency_p50_ms": self._optional_float(kpis.get("latency_p50_ms")),
                "latency_p95_ms": p95_latency,
                "latency_avg_ms": self._optional_float(kpis.get("latency_avg_ms")),
                "total_cost_usd": self._optional_float(kpis.get("total_cost_usd")),
            },
            "failure_rate": failure_rate,
            "suggested_actions": hints,
            "context": {
                "prompt_version_id": run.prompt_version_id,
                "model_config_id": run.model_config_id,
                "dataset_version_id": run.dataset_version_id,
            },
        }
        return payload

    @staticmethod
    def _to_mapping(value: object) -> Mapping[str, object]:
        if isinstance(value, Mapping):
            return {str(key): item for key, item in value.items()}
        return {}

    @staticmethod
    def _failure_rate(examples: Mapping[str, object]) -> float:
        total = PromptOptimizationHookService._optional_int(examples.get("total")) or 0
        failed = PromptOptimizationHookService._optional_int(examples.get("failed")) or 0
        if total <= 0:
            return 0.0
        return failed / total

    @staticmethod
    def _optional_float(value: object) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float, str)):
            return float(value)
        return None

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if value is None:
            return None
        if isinstance(value, (int, float, str)):
            return int(value)
        return None
