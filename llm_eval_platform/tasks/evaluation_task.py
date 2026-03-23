from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class EvaluationTask:
    run_id: UUID
    example_index: int
    input_payload: dict[str, Any]
    expected_output: dict[str, Any] | None
    prompt_template: str
    model_provider: str
    model_name: str
    model_parameters: dict[str, Any]
    metrics: list[str]

    def to_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["run_id"] = str(self.run_id)
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> EvaluationTask:
        return cls(
            run_id=UUID(str(payload["run_id"])),
            example_index=int(payload["example_index"]),
            input_payload=dict(payload.get("input_payload") or {}),
            expected_output=payload.get("expected_output"),
            prompt_template=str(payload["prompt_template"]),
            model_provider=str(payload["model_provider"]),
            model_name=str(payload["model_name"]),
            model_parameters=dict(payload.get("model_parameters") or {}),
            metrics=[str(metric) for metric in payload.get("metrics") or []],
        )