from __future__ import annotations

from typing import Any

from llm_eval_platform.services.evaluation_engine.metric_runner import MetricRunner
from llm_eval_platform.services.evaluation_engine.prompt_renderer import PromptRenderer
from llm_eval_platform.services.model_gateway.base_client import BaseModelClient
from llm_eval_platform.services.model_gateway.mock_client import MockModelClient
from llm_eval_platform.services.model_gateway.openai_client import OpenAIClient
from llm_eval_platform.tasks.evaluation_task import EvaluationTask


class EvaluationEngine:
    def __init__(
        self,
        prompt_renderer: PromptRenderer | None = None,
        metric_runner: MetricRunner | None = None,
    ) -> None:
        self.prompt_renderer = prompt_renderer or PromptRenderer()
        self.metric_runner = metric_runner or MetricRunner()

    def execute(self, task: EvaluationTask) -> dict[str, Any]:
        prompt = self.prompt_renderer.render(task.prompt_template, task.input_payload)
        client = self._resolve_client(task.model_provider)
        model_response = client.generate(
            prompt=prompt,
            model_name=task.model_name,
            parameters=task.model_parameters,
            input_payload=task.input_payload,
            expected_output=task.expected_output,
        )
        actual_output = {"answer": model_response.output_text}
        metric_scores = self.metric_runner.run(
            task.metrics,
            prediction=actual_output,
            reference=task.expected_output,
            context={"input_payload": task.input_payload, "prompt": prompt},
        )
        primary_score = metric_scores.get("exact_match")
        return {
            "example_index": task.example_index,
            "input_payload": task.input_payload,
            "expected_output": task.expected_output,
            "actual_output": actual_output,
            "score": primary_score,
            "status": "completed",
            "metadata": {
                "prompt": prompt,
                "provider": task.model_provider,
                "model_name": task.model_name,
                "metric_scores": metric_scores,
                **model_response.metadata,
            },
            "error_message": None,
        }

    @staticmethod
    def _resolve_client(provider: str) -> BaseModelClient:
        normalized = provider.lower()
        if normalized == "mock":
            return MockModelClient()
        if normalized == "openai":
            return OpenAIClient()
        raise ValueError(f"Unsupported model provider '{provider}'.")