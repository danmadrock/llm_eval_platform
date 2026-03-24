from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class FailureDetails:
    category: str
    stage: str
    retryable: bool
    provider: str | None = None
    attempts: int = 1
    retry_history: list[dict[str, Any]] = field(default_factory=list)

    def to_metadata(self) -> dict[str, Any]:
        return asdict(self)


class EvaluationFailure(Exception):
    def __init__(self, message: str, *, details: FailureDetails) -> None:
        super().__init__(message)
        self.details = details


class MetricExecutionError(Exception):
    pass


def classify_failure(exc: BaseException, *, provider: str | None, stage: str) -> FailureDetails:
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()

    if isinstance(exc, EvaluationFailure):
        return exc.details
    if isinstance(exc, MetricExecutionError):
        return FailureDetails(category="metric_execution_error", stage=stage, retryable=False)
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)) or "timeout" in name:
        return FailureDetails(
            category="provider_timeout",
            stage=stage,
            retryable=True,
            provider=provider,
        )
    if "ratelimit" in name or "rate limit" in message:
        return FailureDetails(
            category="provider_rate_limit",
            stage=stage,
            retryable=True,
            provider=provider,
        )
    if "connection" in name or "connect" in message:
        return FailureDetails(
            category="provider_connection_error",
            stage=stage,
            retryable=True,
            provider=provider,
        )
    if "authentication" in name or "permission" in name or "unauthorized" in message:
        return FailureDetails(
            category="provider_auth_error",
            stage=stage,
            retryable=False,
            provider=provider,
        )
    if isinstance(exc, ValueError) and "unsupported" in message:
        return FailureDetails(
            category="configuration_error",
            stage=stage,
            retryable=False,
            provider=provider,
        )
    if isinstance(exc, ValueError):
        return FailureDetails(
            category="validation_error",
            stage=stage,
            retryable=False,
            provider=provider,
        )
    return FailureDetails(
        category="unexpected_error",
        stage=stage,
        retryable=False,
        provider=provider,
    )