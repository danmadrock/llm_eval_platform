from __future__ import annotations

import os

import pytest
from redis import Redis
from rq import SimpleWorker

from llm_eval_platform.workers.queue import get_evaluation_queue


@pytest.mark.skipif(not os.getenv("LIVE_REDIS_URL"), reason="live redis not configured")
def test_live_redis_queue_round_trip(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_URL", os.environ["LIVE_REDIS_URL"])
    queue = get_evaluation_queue()
    connection = Redis.from_url(os.environ["LIVE_REDIS_URL"])
    connection.flushdb()

    job = queue.enqueue("builtins.len", [1, 2, 3])
    worker = SimpleWorker([queue], connection=connection)
    worker.work(burst=True)
    job.refresh()

    assert job.is_finished
    assert job.result == 3