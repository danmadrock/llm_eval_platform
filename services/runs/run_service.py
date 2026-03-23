from __future__ import annotations

from sqlalchemy.orm import Session

from llm_eval_platform.repositories.dataset_repository import DatasetRepository
from llm_eval_platform.repositories.experiment_repository import ExperimentRepository
from llm_eval_platform.repositories.model_repository import ModelRepository
from llm_eval_platform.repositories.prompt_repository import PromptRepository
from llm_eval_platform.repositories.run_repository import RunRepository
from llm_eval_platform.schemas.run import RunCreate, RunUpdate
from llm_eval_platform.services.common import ServiceBase


class RunService(ServiceBase):
    def __init__(
        self,
        repository: RunRepository | None = None,
        experiment_repository: ExperimentRepository | None = None,
        dataset_repository: DatasetRepository | None = None,
        prompt_repository: PromptRepository | None = None,
        model_repository: ModelRepository | None = None,
    ) -> None:
        self.repository = repository or RunRepository()
        self.experiment_repository = experiment_repository or ExperimentRepository()
        self.dataset_repository = dataset_repository or DatasetRepository()
        self.prompt_repository = prompt_repository or PromptRepository()
        self.model_repository = model_repository or ModelRepository()

    def create(self, db: Session, payload: RunCreate):
        self._require(
            self.experiment_repository.get(db, payload.experiment_id), "Experiment not found."
        )
        self._require(
            self.dataset_repository.get_version(db, payload.dataset_version_id),
            "Dataset version not found.",
        )
        self._require(
            self.prompt_repository.get_version(db, payload.prompt_version_id),
            "Prompt version not found.",
        )
        self._require(
            self.model_repository.get(db, payload.model_config_id), "Model config not found."
        )
        run = self.repository.create(db, payload.model_dump())
        self._commit(db)
        return run

    def list(self, db: Session, *, limit: int, offset: int):
        return self.repository.list(db, limit=limit, offset=offset)

    def get(self, db: Session, run_id):
        return self._require(self.repository.get(db, run_id), "Run not found.")

    def update(self, db: Session, run_id, payload: RunUpdate):
        run = self._require(self.repository.get_for_update(db, run_id), "Run not found.")
        run = self.repository.update(db, run, payload.model_dump(exclude_none=True))
        self._commit(db)
        return run

    def delete(self, db: Session, run_id) -> None:
        run = self._require(self.repository.get(db, run_id), "Run not found.")
        self.repository.delete(db, run)
        self._commit(db)
