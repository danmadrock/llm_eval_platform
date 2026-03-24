from __future__ import annotations

from time import perf_counter
from typing import Any

from llm_eval_platform.services.model_gateway.base_client import BaseModelClient, ModelResponse


class MockModelClient(BaseModelClient):
    """Deterministic local adapter used to prove the async evaluation loop."""

    def generate(
        self,
        *,
        prompt: str,
        model_name: str,
        parameters: dict[str, Any],
        input_payload: dict[str, Any],
        expected_output: dict[str, Any] | None,
    ) -> ModelResponse:
        started = perf_counter()
        strategy = str(parameters.get("mock_strategy", "expected_output"))

        if strategy == "expected_output" and expected_output is not None:
            if isinstance(expected_output, dict):
                answer = expected_output.get("answer")
            else:
                answer = expected_output
        elif strategy == "input_field":
            source_field = str(parameters.get("input_field", "question"))
            answer = input_payload.get(source_field, "")
        elif strategy == "template":
            answer = str(parameters.get("response_template", ""))
        else:
            answer = prompt

        latency_ms = round((perf_counter() - started) * 1000, 3)
        prompt_tokens = max(len(prompt.split()), 1)
        completion_tokens = max(len(str(answer).split()), 1)
        return ModelResponse(
            output_text=str(answer),
            metadata={
                "provider": "mock",
                "model_name": model_name,
                "latency_ms": latency_ms,
                "token_usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
                "mock_strategy": strategy,
            },
        )