from __future__ import annotations

from datetime import datetime, timezone

from llm_eval_platform.models.run import Run


class RunProgressTracker:
    def mark_running(self, run: Run) -> None:
        if run.status == "queued":
            run.status = "running"
        if run.started_at is None:
            run.started_at = datetime.now(timezone.utc)

    def mark_result(self, run: Run, *, succeeded: bool) -> None:
        parameters = dict(run.parameters or {})
        parameters["processed_examples"] = int(parameters.get("processed_examples", 0)) + 1
        counter_name = "completed_examples" if succeeded else "failed_examples"
        parameters[counter_name] = int(parameters.get(counter_name, 0)) + 1
        run.parameters = parameters

    def mark_completed_if_finished(self, run: Run) -> None:
        parameters = dict(run.parameters or {})
        total = int(parameters.get("total_examples", 0))
        processed = int(parameters.get("processed_examples", 0))
        failed = int(parameters.get("failed_examples", 0))
        if total == 0:
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            return
        if processed < total:
            return
        run.completed_at = datetime.now(timezone.utc)
        run.status = "failed" if failed else "completed"