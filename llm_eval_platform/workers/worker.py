from __future__ import annotations

from rq import Connection, Worker

from llm_eval_platform.tasks.task_types import EVALUATION_QUEUE_NAME
from llm_eval_platform.workers.queue import get_redis_connection


def run_worker() -> None:
    connection = get_redis_connection()
    with Connection(connection):
        worker = Worker([EVALUATION_QUEUE_NAME])
        worker.work()


if __name__ == "__main__":
    run_worker()