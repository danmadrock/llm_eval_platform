from __future__ import annotations

from typing import Any

from llm_eval_platform.services.metrics.base_metric import BaseMetric
from llm_eval_platform.services.metrics.semantic_similarity import SemanticSimilarityMetric


class LLMJudgeMetric(BaseMetric):
    name = "llm_judge"
    experimental = True

    def compute(
        self,
        *,
        prediction: Any,
        reference: Any,
        context: dict[str, Any] | None = None,
    ) -> float:
        # Experimental heuristic placeholder until an external judge model is wired in.
        similarity = SemanticSimilarityMetric().compute(
            prediction=prediction,
            reference=reference,
            context=context,
        )
        return round((similarity * 0.7) + (0.3 if similarity > 0.5 else 0.0), 4)