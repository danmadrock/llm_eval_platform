from __future__ import annotations

from sqlalchemy import select
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
            )
            .where(Run.id == run_id)
        )
        return db.scalar(stmt)