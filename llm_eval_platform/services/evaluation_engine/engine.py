from __future__ import annotations

from typing import Any, TypedDict

from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from llm_eval_platform.core.logging import get_logger
from llm_eval_platform.core.observability import metrics
from llm_eval_platform.services.evaluation_engine.failures import (
    EvaluationFailure,
    classify_failure,
)
from llm_eval_platform.services.evaluation_engine.metric_runner import MetricRunner
from llm_eval_platform.services.evaluation_engine.prompt_renderer import PromptRenderer
from llm_eval_platform.services.model_gateway.anthropic_client import AnthropicClient
from llm_eval_platform.services.model_gateway.base_client import BaseModelClient
from llm_eval_platform.services.model_gateway.huggingface_client import HuggingFaceClient
from llm_eval_platform.services.model_gateway.local_vllm_client import LocalVLLMClient
from llm_eval_platform.services.model_gateway.mock_client import MockModelClient
from llm_eval_platform.services.model_gateway.openai_client import OpenAIClient
from llm_eval_platform.tasks.evaluation_task import EvaluationTask

logger = get_logger(__name__)


class RetryPolicy(TypedDict):
    max_attempts: int
    backoff_seconds: float
    max_backoff_seconds: float


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
        idempotency_key = task.idempotency_key()

        retry_policy = self._resolve_retry_policy(task.model_parameters)
        retry_history: list[dict[str, Any]] = []
        attempt_count = 0

        def _should_retry(exc: BaseException) -> bool:
            if not isinstance(exc, Exception):
                return False
            details = classify_failure(
                exc,
                provider=task.model_provider,
                stage="model_inference",
            )
            return details.retryable

        def _before_sleep(retry_state) -> None:
            if retry_state.outcome is None or retry_state.outcome.failed is False:
                return
            exception = retry_state.outcome.exception()
            if exception is None:
                return
            details = classify_failure(
                exception,
                provider=task.model_provider,
                stage="model_inference",
            )
            retry_history.append(
                {
                    "attempt": retry_state.attempt_number,
                    "category": details.category,
                    "retryable": details.retryable,
                    "error": str(exception),
                }
            )
            metrics.inc(
                "evaluation_retry_attempts_total",
                labels={
                    "provider": task.model_provider,
                    "category": details.category,
                    "stage": details.stage,
                },
            )
            logger.warning(
                "evaluation.retry.scheduled",
                run_id=str(task.run_id),
                example_index=task.example_index,
                attempt=retry_state.attempt_number,
                category=details.category,
                provider=task.model_provider,
                idempotency_key=idempotency_key,
            )
            
        model_response = None
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(retry_policy["max_attempts"]),
                wait=wait_exponential(
                    multiplier=retry_policy["backoff_seconds"],
                    min=retry_policy["backoff_seconds"],
                    max=retry_policy["max_backoff_seconds"],
                ),
                retry=retry_if_exception(_should_retry),
                before_sleep=_before_sleep,
                reraise=True,
            ):
                with attempt:
                    attempt_count += 1
                    model_response = client.generate(
                        prompt=prompt,
                        model_name=task.model_name,
                        parameters=task.model_parameters,
                        input_payload=task.input_payload,
                        expected_output=task.expected_output,
                        idempotency_key=idempotency_key,

                    )
        except Exception as exc:  # noqa: BLE001
            details = classify_failure(exc, provider=task.model_provider, stage="model_inference")
            details.attempts = attempt_count or 1
            details.retry_history = retry_history
            metrics.inc(
                "evaluation_failures_total",
                labels={
                    "provider": task.model_provider,
                    "category": details.category,
                    "stage": details.stage,
                },
            )
            raise EvaluationFailure(str(exc), details=details) from exc
        
        if model_response is None:
            raise RuntimeError("Model response was not generated")
        
        context = {
            "input_payload": task.input_payload,
            "prompt": prompt,
            "latency_ms": model_response.metadata.get("latency_ms"),
            "cost_usd": model_response.metadata.get("cost_usd"),
            "provider_metadata": model_response.metadata,
        }
        configured_metrics = self._resolve_metric_set(task.metrics)
        actual_output = {"answer": model_response.output_text}
        try:
            metric_scores = self.metric_runner.run(
                configured_metrics,
                prediction=actual_output,
                reference=task.expected_output,
                context=context,
            )
        except Exception as exc:  # noqa: BLE001
            details = classify_failure(exc, provider=task.model_provider, stage="metric_evaluation")
            details.attempts = attempt_count or 1
            raise EvaluationFailure(str(exc), details=details) from exc
        
        primary_score = metric_scores.get("exact_match")
        metadata = {
            "prompt": prompt,
            "provider": task.model_provider,
            "model_name": task.model_name,
            "metric_scores": metric_scores,
            "retry_policy": retry_policy,
            "attempt_count": attempt_count or 1,
            "retry_count": max((attempt_count or 1) - 1, 0),
            "retry_history": retry_history,
            "idempotency_key": idempotency_key,
            **model_response.metadata,
        }
        logger.info(
            "evaluation.completed",
            run_id=str(task.run_id),
            example_index=task.example_index,
            provider=task.model_provider,
            attempts=attempt_count or 1,
            retry_count=max((attempt_count or 1) - 1, 0),
            idempotency_key=idempotency_key,
            metric_names=sorted(metric_scores.keys()),
        )
        return {
            "example_index": task.example_index,
            "input_payload": task.input_payload,
            "expected_output": task.expected_output,
            "actual_output": actual_output,
            "score": primary_score,
            "status": "completed",
            "metadata": metadata,
            "error_message": None,
        }

    @staticmethod
    def _resolve_client(provider: str) -> BaseModelClient:
        normalized = provider.lower()
        if normalized == "mock":
            return MockModelClient()
        if normalized == "openai":
            return OpenAIClient()
        if normalized == "anthropic":
            return AnthropicClient()
        if normalized == "huggingface":
            return HuggingFaceClient()
        if normalized in {"local_vllm", "vllm"}:
            return LocalVLLMClient()
        raise ValueError(f"Unsupported model provider '{provider}'.")

    @staticmethod
    def _resolve_retry_policy(parameters: dict[str, Any]) -> RetryPolicy:
        retry_overrides = dict(parameters.get("retry_policy") or {})
        max_attempts = max(int(retry_overrides.get("max_attempts", 3)), 1)
        backoff_seconds = max(float(retry_overrides.get("backoff_seconds", 0.25)), 0.0)
        max_backoff_seconds = max(
            float(retry_overrides.get("max_backoff_seconds", 2.0)),
            backoff_seconds,
        )
        return {
            "max_attempts": max_attempts,
            "backoff_seconds": backoff_seconds,
            "max_backoff_seconds": max_backoff_seconds,
        }

    @staticmethod
    def _resolve_metric_set(configured: list[str]) -> list[str]:
        base = {"exact_match", "semantic_similarity", "latency", "cost", "llm_judge"}
        requested = {str(metric) for metric in configured}
        if "llm_judge_experimental" in requested:
            requested.add("llm_judge")
        return sorted(base | requested)