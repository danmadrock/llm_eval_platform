from __future__ import annotations

from time import perf_counter
from typing import Any

from anthropic import Anthropic

from llm_eval_platform.services.model_gateway.base_client import BaseModelClient, ModelResponse


class AnthropicClient(BaseModelClient):
    def __init__(self, client: Anthropic | None = None) -> None:
        self.client = client or Anthropic()

    def generate(
        self,
        *,
        prompt: str,
        model_name: str,
        parameters: dict[str, Any],
        input_payload: dict[str, Any],
        expected_output: dict[str, Any] | None,
        idempotency_key: str | None = None,
    ) -> ModelResponse:
        started = perf_counter()
        response = self.client.messages.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=parameters.get("temperature", 0),
            max_tokens=parameters.get("max_tokens", 512),
        )
        latency_ms = round((perf_counter() - started) * 1000, 3)
        output_text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        total_tokens = None
        if input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens
        return ModelResponse(
            output_text=output_text,
            metadata={
                "provider": "anthropic",
                "model_name": model_name,
                "latency_ms": latency_ms,
                "token_usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": total_tokens,
                },
            },
        )