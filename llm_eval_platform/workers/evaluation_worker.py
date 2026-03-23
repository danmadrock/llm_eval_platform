from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from llm_eval_platform.core.database import SessionLocal
from llm_eval_platform.models.evaluation_result import EvaluationResult
from llm_eval_platform.models.run import Run
from llm_eval_platform.services.evaluation_engine.engine import EvaluationEngine
from llm_eval_platform.services.runs.run_aggregator import RunAggregator
from llm_eval_platform.services.runs.run_progress_tracker import RunProgressTracker
from llm_eval_platform.tasks.evaluation_task import EvaluationTask


def process_evaluation_task(payload: dict) -> dict:
    task = EvaluationTask.from_payload(payload)
    with SessionLocal() as db:
        run = db.scalar(
            select(Run).options(selectinload(Run.evaluation_results)).where(Run.id == task.run_id)
        )
        if run is None:
            raise ValueError(f"Run {task.run_id} was not found.")

        tracker = RunProgressTracker()
        aggregator = RunAggregator()
        engine = EvaluationEngine()

        tracker.mark_running(run)
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            execution_result = engine.execute(task)
            persisted = _upsert_result(db, run, execution_result)
            tracker.mark_result(run, succeeded=True)
            aggregator.update_summary(db, run)
            tracker.mark_completed_if_finished(run)
            db.add(run)
            db.commit()
            db.refresh(run)
            return {
                "run_id": str(run.id),
                "result_id": str(persisted.id),
                "status": run.status,
                "example_index": task.example_index,
            }
        except Exception as exc:  # noqa: BLE001
            persisted = _upsert_result(
                db,
                run,
                {
                    "example_index": task.example_index,
                    "input_payload": task.input_payload,
                    "expected_output": task.expected_output,
                    "actual_output": None,
                    "score": 0.0,
                    "status": "failed",
                    "metadata": {"provider": task.model_provider, "model_name": task.model_name},
                    "error_message": str(exc),
                },
            )
            tracker.mark_result(run, succeeded=False)
            run.error_message = str(exc)
            aggregator.update_summary(db, run)
            tracker.mark_completed_if_finished(run)
            db.add(run)
            db.commit()
            db.refresh(run)
            return {
                "run_id": str(run.id),
                "result_id": str(persisted.id),
                "status": run.status,
                "example_index": task.example_index,
                "error": str(exc),
            }


def _upsert_result(db, run: Run, execution_result: dict) -> EvaluationResult:
    existing = next(
        (
            result
            for result in run.evaluation_results
            if result.example_index == execution_result["example_index"]
        ),
        None,
    )
    if existing is None:
        existing = EvaluationResult(
            run_id=run.id,
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
    db.flush()
    if existing not in run.evaluation_results:
        run.evaluation_results.append(existing)
    db.refresh(existing)
    return existing
