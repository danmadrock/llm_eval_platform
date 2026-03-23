from __future__ import annotations

from typing import Any

from llm_eval_platform.services.metrics.exact_match import ExactMatchMetric


class MetricRunner:
    def __init__(self) -> None:
        self._registry = {ExactMatchMetric.name: ExactMatchMetric()}

    def run(
        self,
        metric_names: list[str],
        *,
        prediction: Any,
        reference: Any,
        context: dict[str, Any] | None = None,
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        for metric_name in metric_names:
            metric = self._registry.get(metric_name)
            if metric is None:
                raise ValueError(f"Unsupported metric '{metric_name}'.")
            scores[metric_name] = metric.compute(
                prediction=prediction,
                reference=reference,
                context=context,
            )
        return scores