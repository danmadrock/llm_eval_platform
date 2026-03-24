from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from llm_eval_platform.core.database import SessionLocal
from llm_eval_platform.core.logging import get_logger
from llm_eval_platform.core.observability import metrics
from llm_eval_platform.models.evaluation_result import EvaluationResult
from llm_eval_platform.models.run import Run
from llm_eval_platform.services.evaluation_engine.engine import EvaluationEngine
from llm_eval_platform.services.evaluation_engine.failures import (
    EvaluationFailure,
    classify_failure,
)
from llm_eval_platform.services.runs.run_aggregator import RunAggregator
from llm_eval_platform.services.runs.run_progress_tracker import RunProgressTracker
from llm_eval_platform.tasks.evaluation_task import EvaluationTask


logger = get_logger(__name__)

def process_evaluation_task(payload: dict) -> dict:
    task = EvaluationTask.from_payload(payload)
    tracker = RunProgressTracker()
    aggregator = RunAggregator()
    engine = EvaluationEngine()
    with SessionLocal() as db:
        run = db.scalar(select(Run).where(Run.id == task.run_id))

        if run is None:
            raise ValueError(f"Run {task.run_id} was not found.")
        tracker.mark_running(db, run.id)
        db.commit()

        try:
            execution_result = engine.execute(task)
            persisted = _upsert_result(db, task.run_id, execution_result)
            tracker.record_result(db, task.run_id, succeeded=True)
            aggregator.update_summary(db, task.run_id)
            db.commit()
            db.refresh(persisted)
            run = db.scalar(select(Run).where(Run.id == task.run_id))
            logger.info(
                "evaluation.result.persisted",
                run_id=str(task.run_id),
                example_index=task.example_index,
                result_id=str(persisted.id),
                status="completed",
                idempotency_key=task.idempotency_key(),
            )
            return {
                "run_id": str(task.run_id),
                "result_id": str(persisted.id),
                "status": run.status if run is not None else "running",
                "example_index": task.example_index,
            }
        except Exception as exc:  # noqa: BLE001
            details = (
                exc.details
                if isinstance(exc, EvaluationFailure)
                else classify_failure(
                    exc,
                    provider=task.model_provider,
                    stage="worker",
                )
            )
            persisted = _upsert_result(
                db,
                task.run_id,
                {
                    "example_index": task.example_index,
                    "input_payload": task.input_payload,
                    "expected_output": task.expected_output,
                    "actual_output": None,
                    "score": 0.0,
                    "status": "failed",
                    "metadata": {
                        "provider": task.model_provider,
                        "model_name": task.model_name,
                        "failure": details.to_metadata(),
                    },
                    "error_message": str(exc),
                },
            )
            tracker.record_result(
                db,
                task.run_id,
                succeeded=False,
                error_message=f"{details.category}: {exc}",
            )
            aggregator.update_summary(db, task.run_id)
            db.commit()
            db.refresh(persisted)
            run = db.scalar(select(Run).where(Run.id == task.run_id))
            metrics.inc(
                "evaluation_failures_total",
                labels={
                    "provider": task.model_provider,
                    "category": details.category,
                    "stage": details.stage,
                },
            )
            logger.error(
                "evaluation.failed",
                run_id=str(task.run_id),
                example_index=task.example_index,
                provider=task.model_provider,
                category=details.category,
                stage=details.stage,
                retryable=details.retryable,
                attempts=details.attempts,
                idempotency_key=task.idempotency_key(),
                error=str(exc),
            )
            return {
                "run_id": str(task.run_id),
                "result_id": str(persisted.id),
                "status": run.status if run is not None else "failed",
                "example_index": task.example_index,
                "error": str(exc),
                "failure": details.to_metadata(),
            }


def _upsert_result(db, run_id, execution_result: dict) -> EvaluationResult:
    existing = db.scalar(
        select(EvaluationResult).where(
            EvaluationResult.run_id == run_id,
            EvaluationResult.example_index == execution_result["example_index"],
        )
    )
    if existing is None:
        existing = EvaluationResult(
            run_id=run_id,
            example_index=execution_result["example_index"],
        )
    existing.input_payload = execution_result["input_payload"]
    existing.expected_output = execution_result["expected_output"]
    existing.actual_output = execution_result["actual_output"]
    existing.score = execution_result["score"]
    existing.status = execution_result["status"]
    existing.result_metadata = execution_result["metadata"]
    existing.error_message = execution_result["error_message"]
    db.add(existing)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(EvaluationResult).where(
                EvaluationResult.run_id == run_id,
                EvaluationResult.example_index == execution_result["example_index"],
            )
        )
        if existing is None:
            raise
        existing.input_payload = execution_result["input_payload"]
        existing.expected_output = execution_result["expected_output"]
        existing.actual_output = execution_result["actual_output"]
        existing.score = execution_result["score"]
        existing.status = execution_result["status"]
        existing.result_metadata = execution_result["metadata"]
        existing.error_message = execution_result["error_message"]
        db.add(existing)
        db.flush()
    db.refresh(existing)
    return existing
