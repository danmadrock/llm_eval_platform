from __future__ import annotations

from typing import Any

from llm_eval_platform.services.metrics.base_metric import BaseMetric


class CostMetric(BaseMetric):
    name = "cost"

    def compute(
        self,
        *,
        prediction: Any,
        reference: Any,
        context: dict[str, Any] | None = None,
    ) -> float:
        if context is None:
            return 0.0
        return float(context.get("cost_usd") or 0.0)