from __future__ import annotations

from sqlalchemy.orm import Session

from llm_eval_platform.repositories.dataset_repository import DatasetRepository
from llm_eval_platform.schemas.dataset import DatasetCreate, DatasetUpdate
from llm_eval_platform.services.common import ServiceBase


class DatasetService(ServiceBase):
    def __init__(self, repository: DatasetRepository | None = None) -> None:
        self.repository = repository or DatasetRepository()

    def create(self, db: Session, payload: DatasetCreate):
        dataset = self.repository.create(db, payload.model_dump())
        self._commit(db)
        return self.repository.get_with_versions(db, dataset.id)

    def list(self, db: Session, *, limit: int, offset: int):
        return self.repository.list(db, limit=limit, offset=offset)

    def get(self, db: Session, dataset_id):
        return self._require(
            self.repository.get_with_versions(db, dataset_id), "Dataset not found."
        )

    def update(self, db: Session, dataset_id, payload: DatasetUpdate):
        dataset = self._require(self.repository.get(db, dataset_id), "Dataset not found.")
        dataset = self.repository.update(db, dataset, payload.model_dump(exclude_none=True))
        self._commit(db)
        return self.repository.get_with_versions(db, dataset.id)

    def delete(self, db: Session, dataset_id) -> None:
        dataset = self._require(self.repository.get(db, dataset_id), "Dataset not found.")
        self.repository.delete(db, dataset)
        self._commit(db)