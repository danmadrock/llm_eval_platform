from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ModelResponse:
    output_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseModelClient(ABC):
    @abstractmethod
    def generate(
        self,
        *,
        prompt: str,
        model_name: str,
        parameters: dict[str, Any],
        input_payload: dict[str, Any],
        expected_output: dict[str, Any] | None,
    ) -> ModelResponse:
        raise NotImplementedError