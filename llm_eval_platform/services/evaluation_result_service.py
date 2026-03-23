from __future__ import annotations

from sqlalchemy.orm import Session

from llm_eval_platform.repositories.result_repository import ResultRepository
from llm_eval_platform.repositories.run_repository import RunRepository
from llm_eval_platform.schemas.result import EvaluationResultCreate, EvaluationResultUpdate
from llm_eval_platform.services.common import ServiceBase


class EvaluationResultService(ServiceBase):
    def __init__(
        self,
        repository: ResultRepository | None = None,
        run_repository: RunRepository | None = None,
    ) -> None:
        self.repository = repository or ResultRepository()
        self.run_repository = run_repository or RunRepository()

    def create(self, db: Session, payload: EvaluationResultCreate):
        self._require(self.run_repository.get(db, payload.run_id), "Run not found.")
        result = self.repository.create(db, payload.model_dump())
        self._commit(db)
        return result

    def list(self, db: Session, *, limit: int, offset: int, run_id=None):
        if run_id is None:
            return self.repository.list(db, limit=limit, offset=offset)
        self._require(self.run_repository.get(db, run_id), "Run not found.")
        return self.repository.list_by_run(db, run_id, limit=limit, offset=offset)

    def get(self, db: Session, result_id):
        return self._require(self.repository.get(db, result_id), "Evaluation result not found.")

    def update(self, db: Session, result_id, payload: EvaluationResultUpdate):
        result = self._require(self.repository.get(db, result_id), "Evaluation result not found.")
        result = self.repository.update(db, result, payload.model_dump(exclude_none=True))
        self._commit(db)
        return result

    def delete(self, db: Session, result_id) -> None:
        result = self._require(self.repository.get(db, result_id), "Evaluation result not found.")
        self.repository.delete(db, result)
        self._commit(db)