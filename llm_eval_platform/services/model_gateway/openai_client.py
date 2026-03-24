from __future__ import annotations

from time import perf_counter
from typing import Any

from openai import OpenAI

from llm_eval_platform.services.model_gateway.base_client import BaseModelClient, ModelResponse


class OpenAIClient(BaseModelClient):
    def __init__(self, client: OpenAI | None = None) -> None:
        self.client = client or OpenAI()

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
        response = self.client.responses.create( # type: ignore
            model=model_name,
            input=prompt,
            temperature=parameters.get("temperature", 0),
            max_output_tokens=parameters.get("max_tokens"),
        )
        latency_ms = round((perf_counter() - started) * 1000, 3)
        output_text = response.output_text
        usage = getattr(response, "usage", None)
        return ModelResponse(
            output_text=output_text,
            metadata={
                "provider": "openai",
                "model_name": model_name,
                "latency_ms": latency_ms,
                "token_usage": {
                    "prompt_tokens": getattr(usage, "input_tokens", None),
                    "completion_tokens": getattr(usage, "output_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                },
            },
        )
    