from __future__ import annotations

from time import perf_counter
from typing import Any

from openai import OpenAI

from llm_eval_platform.services.model_gateway.base_client import BaseModelClient, ModelResponse


class LocalVLLMClient(BaseModelClient):
    def __init__(self, client: OpenAI | None = None, *, base_url: str | None = None) -> None:
        self.client = client or OpenAI(
            base_url=base_url or "http://localhost:8000/v1",
            api_key="local-vllm",
        )

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
        response = self.client.responses.create( # type: ignore
            model=model_name,
            input=prompt,
            temperature=parameters.get("temperature", 0),
            max_output_tokens=parameters.get("max_tokens"),
            idempotency_key=idempotency_key,
        )
        latency_ms = round((perf_counter() - started) * 1000, 3)
        return ModelResponse(
            output_text=response.output_text,

            metadata={
                "provider": "local_vllm",
                "model_name": model_name,
                "latency_ms": latency_ms,
            },
        )
