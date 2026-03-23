from __future__ import annotations

from sqlalchemy.orm import Session

from llm_eval_platform.repositories.prompt_repository import PromptRepository
from llm_eval_platform.schemas.prompt import PromptVersionCreate
from llm_eval_platform.services.common import ServiceBase


class PromptVersionService(ServiceBase):
    def __init__(self, repository: PromptRepository | None = None) -> None:
        self.repository = repository or PromptRepository()

    def create(self, db: Session, prompt_id, payload: PromptVersionCreate):
        self._require(self.repository.get(db, prompt_id), "Prompt not found.")
        version = self.repository.create_version(db, prompt_id, **payload.model_dump())
        self._commit(db)
        return version

    def list(self, db: Session, prompt_id):
        self._require(self.repository.get(db, prompt_id), "Prompt not found.")
        return self.repository.list_versions(db, prompt_id)