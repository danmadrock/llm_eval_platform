from __future__ import annotations

from typing import Any

from llm_eval_platform.services.metrics.base_metric import BaseMetric


class SemanticSimilarityMetric(BaseMetric):
    name = "semantic_similarity"

    def compute(
        self,
        *,
        prediction: Any,
        reference: Any,
        context: dict[str, Any] | None = None,
    ) -> float:
        prediction_tokens = self._tokenize(prediction)
        reference_tokens = self._tokenize(reference)
        if not prediction_tokens and not reference_tokens:
            return 1.0
        union = prediction_tokens | reference_tokens
        if not union:
            return 0.0
        overlap = prediction_tokens & reference_tokens
        return len(overlap) / len(union)

    @staticmethod
    def _tokenize(value: Any) -> set[str]:
        if value is None:
            return set()
        if isinstance(value, dict) and "answer" in value:
            value = value["answer"]
        normalized = " ".join(str(value).lower().split())
        return {token for token in normalized.split(" ") if token}