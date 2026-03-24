from __future__ import annotations

from typing import Any

from llm_eval_platform.services.metrics.base_metric import BaseMetric


class LatencyMetric(BaseMetric):
    name = "latency"

    def compute(
        self,
        *,
        prediction: Any,
        reference: Any,
        context: dict[str, Any] | None = None,
    ) -> float:
        if context is None:
            return 0.0
        return float(context.get("latency_ms") or 0.0)