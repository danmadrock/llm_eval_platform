from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from llm_eval_platform.models.run import Run
from llm_eval_platform.repositories.base_repository import BaseRepository


class RunRepository(BaseRepository[Run]):
    def __init__(self) -> None:
        super().__init__(Run)

    def get_for_update(self, db: Session, run_id):
        return db.get(Run, run_id)

    def get_with_relations(self, db: Session, run_id):
        stmt = (
            select(Run)
            .options(
                selectinload(Run.dataset_version),
                selectinload(Run.prompt_version),
                selectinload(Run.model_config),
                selectinload(Run.evaluation_results),
                selectinload(Run.metrics),
            )
            .where(Run.id == run_id)
        )
        return db.scalar(stmt)

    def list(self, db: Session, *, limit: int, offset: int):
        stmt = (
            select(Run)
            .options(selectinload(Run.metrics))
            .order_by(Run.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = db.scalars(stmt).all()
        total = db.scalar(select(func.count()).select_from(Run)) or 0
        return items, total