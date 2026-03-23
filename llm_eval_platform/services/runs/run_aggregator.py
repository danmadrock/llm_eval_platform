from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from llm_eval_platform.models.evaluation_result import EvaluationResult
from llm_eval_platform.models.run import Run


class RunAggregator:
    def update_summary(self, db: Session, run: Run) -> None:
        average_score = db.scalar(
            select(func.avg(EvaluationResult.score)).where(EvaluationResult.run_id == run.id)
        )
        status_breakdown_rows = db.execute(
            select(EvaluationResult.status, func.count())
            .where(EvaluationResult.run_id == run.id)
            .group_by(EvaluationResult.status)
        ).all()
        status_breakdown = {status: count for status, count in status_breakdown_rows}
        parameters = dict(run.parameters or {})
        parameters["summary"] = {
            "average_score": float(average_score) if average_score is not None else None,
            "status_breakdown": status_breakdown,
        }
        run.parameters = parameters