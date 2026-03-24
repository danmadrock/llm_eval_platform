from __future__ import annotations

from time import perf_counter
from typing import Any

from huggingface_hub import InferenceClient

from llm_eval_platform.services.model_gateway.base_client import BaseModelClient, ModelResponse


class HuggingFaceClient(BaseModelClient):
    def __init__(self, client: InferenceClient | None = None) -> None:
        self.client = client or InferenceClient()

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
        output_text = self.client.text_generation(
            prompt,
            model=model_name,
            max_new_tokens=parameters.get("max_tokens", 256),
            temperature=parameters.get("temperature", 0),
        )
        latency_ms = round((perf_counter() - started) * 1000, 3)
        return ModelResponse(
            output_text=str(output_text),
            metadata={
                "provider": "huggingface",
                "model_name": model_name,
                "latency_ms": latency_ms,
            },
        )