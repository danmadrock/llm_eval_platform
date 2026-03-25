from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from llm_eval_platform.services.evaluation_engine.failures import MetricExecutionError
from llm_eval_platform.services.metrics.base_metric import BaseMetric
from llm_eval_platform.services.metrics.cost_metric import CostMetric
from llm_eval_platform.services.metrics.exact_match import ExactMatchMetric
from llm_eval_platform.services.metrics.latency_metric import LatencyMetric
from llm_eval_platform.services.metrics.llm_judge import LLMJudgeMetric
from llm_eval_platform.services.metrics.semantic_similarity import SemanticSimilarityMetric


class MetricRunner:
    def __init__(self, metrics: Iterable[BaseMetric] | None = None) -> None:
        metric_plugins = metrics or [
            ExactMatchMetric(),
            SemanticSimilarityMetric(),
            LatencyMetric(),
            CostMetric(),
            LLMJudgeMetric(),
        ]
        self._registry = {metric.name: metric for metric in metric_plugins}
        if "llm_judge" in self._registry:
            self._registry["llm_judge_experimental"] = self._registry["llm_judge"]

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
                raise MetricExecutionError(f"Unsupported metric '{metric_name}'.")
            try:
                scores[metric_name] = metric.compute(
                    prediction=prediction,
                    reference=reference,
                    context=context,
                )
            except Exception as exc:  # noqa: BLE001
                raise MetricExecutionError(
                    f"Metric '{metric_name}' execution failed: {exc}"
                ) from exc
        return scores