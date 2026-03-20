from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.evaluation_result import EvaluationResult
from repositories.base_repository import BaseRepository


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
        total = len(
            db.scalars(select(EvaluationResult.id).where(EvaluationResult.run_id == run_id)).all()
        )
        return items, total