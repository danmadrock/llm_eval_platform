from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from llm_eval_platform.models.evaluation_result import EvaluationResult
from llm_eval_platform.repositories.base_repository import BaseRepository


class ResultRepository(BaseRepository[EvaluationResult]):
    def __init__(self) -> None:
        super().__init__(EvaluationResult)

    def list_by_run(self, db: Session, run_id, *, limit: int, offset: int):
        stmt = (
            select(EvaluationResult)
            .where(EvaluationResult.run_id == run_id)
            .order_by(EvaluationResult.example_index)
            .offset(offset)
            .limit(limit)
        )
        items = db.scalars(stmt).all()
        total_stmt = (
            select(func.count())
            .select_from(EvaluationResult)
            .where(EvaluationResult.run_id == run_id)
        )
        total = db.scalar(total_stmt) or 0
        return items, total