from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID
from hashlib import sha256


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

    def idempotency_key(self) -> str:
        identity = {
            "run_id": str(self.run_id),
            "example_index": self.example_index,
            "provider": self.model_provider,
            "model": self.model_name,
            "input": self.input_payload,
            "expected_output": self.expected_output,
        }
        digest = sha256(repr(sorted(identity.items())).encode("utf-8")).hexdigest()
        return f"eval:{digest}"
    
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