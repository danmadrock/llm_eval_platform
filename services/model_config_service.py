from __future__ import annotations

from sqlalchemy.orm import Session

from repositories.model_repository import ModelRepository
from schemas.model_config import ModelConfigCreate, ModelConfigUpdate
from services.common import ServiceBase


class ModelConfigService(ServiceBase):
    def __init__(self, repository: ModelRepository | None = None) -> None:
        self.repository = repository or ModelRepository()

    def create(self, db: Session, payload: ModelConfigCreate):
        model_config = self.repository.create(db, payload.model_dump())
        self._commit(db)
        return model_config

    def list(self, db: Session, *, limit: int, offset: int):
        return self.repository.list(db, limit=limit, offset=offset)

    def get(self, db: Session, model_config_id):
        return self._require(self.repository.get(db, model_config_id), "Model config not found.")

    def update(self, db: Session, model_config_id, payload: ModelConfigUpdate):
        model_config = self._require(
            self.repository.get(db, model_config_id), "Model config not found."
        )
        model_config = self.repository.update(
            db, model_config, payload.model_dump(exclude_none=True)
        )
        self._commit(db)
        return model_config

    def delete(self, db: Session, model_config_id) -> None:
        model_config = self._require(
            self.repository.get(db, model_config_id), "Model config not found."
        )
        self.repository.delete(db, model_config)
        self._commit(db)