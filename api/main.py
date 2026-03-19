from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from core.config import get_settings
from core.database import Base, check_database_health, engine
from core.logging import configure_logging, get_logger

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