from contextlib import asynccontextmanager

import redis
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse


import llm_eval_platform.models  # noqa: F401
from llm_eval_platform.api.middleware import add_http_observability_middleware
from llm_eval_platform.api.routes import (
    dashboard_router,
    datasets_router,
    experiments_router,
    models_router,
    prompt_versions_router,
    prompts_router,
    results_router,
    runs_router,
)
from llm_eval_platform.core.config import get_settings
from llm_eval_platform.core.database import Base, check_database_health, engine
from llm_eval_platform.core.security import bind_tenant_context
from llm_eval_platform.core.exceptions import DomainError
from llm_eval_platform.core.logging import configure_logging, get_logger
from llm_eval_platform.core.observability import metrics

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("application.starting", environment=settings.environment)
    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield
    logger.info("application.stopping")


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
add_http_observability_middleware(app)


@app.exception_handler(DomainError)
async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": exc.errors(),
            }
        },
    )


def check_redis_health() -> bool:
    client = redis.from_url(settings.redis_url)
    try:
        return bool(client.ping())
    finally:
        client.close()


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def readiness() -> JSONResponse:
    services = {"database": False, "redis": False}

    try:
        services["database"] = check_database_health()
    except Exception as exc:  # noqa: BLE001
        logger.warning("health.database.failed", error=str(exc))

    try:
        services["redis"] = check_redis_health()
    except Exception as exc:  # noqa: BLE001
        logger.warning("health.redis.failed", error=str(exc))

    if all(services.values()):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "services": services},
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "not_ready", "services": services},
    )

@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics() -> str:
    return metrics.render()


api_v1_prefix = "/api/v1"
for router in [
    dashboard_router,
    datasets_router,
    prompts_router,
    prompt_versions_router,
    models_router,
    experiments_router,
    runs_router,
    results_router,
]:
    app.include_router(router, prefix=api_v1_prefix, dependencies=[Depends(bind_tenant_context)])