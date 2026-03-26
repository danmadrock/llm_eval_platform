from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from llm_eval_platform.models.run import Run
from llm_eval_platform.repositories.base_repository import BaseRepository


class RunRepository(BaseRepository[Run]):
    def __init__(self) -> None:
        super().__init__(Run)

    def get_for_update(self, db: Session, run_id: Any) -> Run | None:
        stmt = select(Run).where(Run.id == run_id)
        return cast(Run | None, db.scalar(self._tenant_filter(db, stmt)))
    
    def get_with_relations(self, db: Session, run_id: Any) -> Run | None:
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
        return cast(Run | None, db.scalar(self._tenant_filter(db, stmt)))

    def list(self, db: Session, *, limit: int, offset: int) -> tuple[list[Run], int]:
        stmt = (
            select(Run)
            .options(selectinload(Run.metrics))
            .order_by(Run.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        stmt = self._tenant_filter(db, stmt)
        items = list(cast(list[Run], db.scalars(stmt).all()))
        total_stmt = self._tenant_filter(db, select(func.count()).select_from(Run))
        total = int(db.scalar(total_stmt) or 0)
        return items, total

    def count_created_since(self, db: Session, created_after: datetime) -> int:
        stmt = select(func.count()).select_from(Run).where(Run.created_at >= created_after)
        stmt = self._tenant_filter(db, stmt)
        return int(db.scalar(stmt) or 0)