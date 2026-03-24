from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from llm_eval_platform.models.run_metric import RunMetric
from llm_eval_platform.repositories.base_repository import BaseRepository


class RunMetricRepository(BaseRepository[RunMetric]):
    def __init__(self) -> None:
        super().__init__(RunMetric)

    def list_by_run(self, db: Session, run_id):
        stmt = select(RunMetric).where(RunMetric.run_id == run_id).order_by(RunMetric.metric_name)
        return db.scalars(stmt).all()

    def delete_by_run(self, db: Session, run_id) -> None:
        db.execute(delete(RunMetric).where(RunMetric.run_id == run_id))