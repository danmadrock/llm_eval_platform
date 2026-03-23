from __future__ import annotations

from redis import Redis
from rq import Queue

from llm_eval_platform.core.config import get_settings
from llm_eval_platform.tasks.task_types import EVALUATION_JOB_TIMEOUT, EVALUATION_QUEUE_NAME


def get_redis_connection() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def get_evaluation_queue() -> Queue:
    return Queue(
        name=EVALUATION_QUEUE_NAME,
        connection=get_redis_connection(),
        default_timeout=EVALUATION_JOB_TIMEOUT,
    )