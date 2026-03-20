from __future__ import annotations

from sqlalchemy.orm import Session

from repositories.experiment_repository import ExperimentRepository
from schemas.experiment import ExperimentCreate, ExperimentUpdate
from services.common import ServiceBase


class ExperimentService(ServiceBase):
    def __init__(self, repository: ExperimentRepository | None = None) -> None:
        self.repository = repository or ExperimentRepository()

    def create(self, db: Session, payload: ExperimentCreate):
        experiment = self.repository.create(db, payload.model_dump())
        self._commit(db)
        return experiment

    def list(self, db: Session, *, limit: int, offset: int):
        return self.repository.list(db, limit=limit, offset=offset)

    def get(self, db: Session, experiment_id):
        return self._require(self.repository.get(db, experiment_id), "Experiment not found.")

    def update(self, db: Session, experiment_id, payload: ExperimentUpdate):
        experiment = self._require(self.repository.get(db, experiment_id), "Experiment not found.")
        experiment = self.repository.update(db, experiment, payload.model_dump(exclude_none=True))
        self._commit(db)
        return experiment

    def delete(self, db: Session, experiment_id) -> None:
        experiment = self._require(self.repository.get(db, experiment_id), "Experiment not found.")
        self.repository.delete(db, experiment)
        self._commit(db)