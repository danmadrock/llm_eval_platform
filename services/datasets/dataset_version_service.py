from __future__ import annotations

from sqlalchemy.orm import Session

from repositories.dataset_repository import DatasetRepository
from schemas.dataset import DatasetVersionCreate
from services.common import ServiceBase


class DatasetVersionService(ServiceBase):
    def __init__(self, repository: DatasetRepository | None = None) -> None:
        self.repository = repository or DatasetRepository()

    def create(self, db: Session, dataset_id, payload: DatasetVersionCreate):
        self._require(self.repository.get(db, dataset_id), "Dataset not found.")
        version = self.repository.create_version(db, dataset_id, **payload.model_dump())
        self._commit(db)
        return version

    def list(self, db: Session, dataset_id):
        self._require(self.repository.get(db, dataset_id), "Dataset not found.")
        return self.repository.list_versions(db, dataset_id)
