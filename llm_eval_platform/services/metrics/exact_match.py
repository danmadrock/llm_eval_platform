from __future__ import annotations

from typing import Any

from llm_eval_platform.services.metrics.base_metric import BaseMetric


class ExactMatchMetric(BaseMetric):
    name = "exact_match"

    def compute(
        self,
        *,
        prediction: Any,
        reference: Any,
        context: dict[str, Any] | None = None,
    ) -> float:
        return 1.0 if self._normalize(prediction) == self._normalize(reference) else 0.0

    @staticmethod
    def _normalize(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, dict):
            if "answer" in value:
                return ExactMatchMetric._normalize(value["answer"])
            parts = [
                f"{key}:{ExactMatchMetric._normalize(inner)}"
                for key, inner in sorted(value.items())
            ]
            return " ".join(parts).strip()
        if isinstance(value, list):
            return " ".join(ExactMatchMetric._normalize(item) for item in value).strip()
        return " ".join(str(value).strip().split())