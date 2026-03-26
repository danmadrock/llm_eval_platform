from __future__ import annotations

from time import perf_counter

from fastapi import FastAPI, Request

from llm_eval_platform.core.logging import get_logger
from llm_eval_platform.core.observability import metrics

logger = get_logger(__name__)


def add_http_observability_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _observability(request: Request, call_next):
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (perf_counter() - started) * 1000
            route = request.url.path
            method = request.method
            labels = {"method": method, "route": route, "status": str(status_code)}
            metrics.inc("http_requests_total", labels=labels)
            metrics.observe(
                "http_request_duration_ms",
                duration_ms,
                labels={"method": method, "route": route},
            )
            logger.info(
                "http.request.completed",
                method=method,
                route=route,
                status_code=status_code,
                duration_ms=round(duration_ms, 3),
            )