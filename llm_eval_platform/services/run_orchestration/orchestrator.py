from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from llm_eval_platform.core.exceptions import NotFoundError
from llm_eval_platform.models.run import Run
from llm_eval_platform.services.run_orchestration.task_builder import TaskBuilder
from llm_eval_platform.tasks.evaluation_task import EvaluationTask
from llm_eval_platform.tasks.task_types import PROCESS_EVALUATION_TASK_FUNCTION
from llm_eval_platform.workers.queue import get_evaluation_queue


class JobQueue(Protocol):
    def enqueue(self, func: str, *args: Any, **kwargs: Any) -> Any: ...


class RunOrchestrator:
    def __init__(
        self,
        task_builder: TaskBuilder | None = None,
        queue: JobQueue | None = None,
    ) -> None:
        self.task_builder = task_builder or TaskBuilder()
        self.queue = queue or get_evaluation_queue()

    def enqueue_run(self, db: Session, run_id: UUID) -> Run:
        run = self._get_run_with_context(db, run_id)
        tasks = self.task_builder.build_tasks(run)
        total_examples = len(tasks)
        run.parameters = {
            **(run.parameters or {}),
            "metrics": self.task_builder.resolve_metrics(run.parameters or {}),
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
        run.total_examples = total_examples
        run.processed_examples = 0
        run.completed_examples = 0
        run.failed_examples = 0 
        run.status = "queued"
        run.error_message = None
        run.started_at = None
        run.completed_at = None
        run.metrics.clear()
        db.add(run)
        db.commit()
        db.refresh(run)

        for task in tasks:
            self._enqueue_task(task)
        return run

    def _enqueue_task(self, task: EvaluationTask) -> None:
        self.queue.enqueue(PROCESS_EVALUATION_TASK_FUNCTION, task.to_payload())

    @staticmethod
    def _get_run_with_context(db: Session, run_id: UUID) -> Run:
        stmt = (
            select(Run)
            .options(
                selectinload(Run.dataset_version),
                selectinload(Run.prompt_version),
                selectinload(Run.model_config),
                selectinload(Run.metrics),
            )
            .where(Run.id == run_id)
        )
        run = db.scalar(stmt)
        if run is None:
            raise NotFoundError("Run not found.")
        return run