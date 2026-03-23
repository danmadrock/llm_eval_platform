from __future__ import annotations

from sqlalchemy.orm import Session

from llm_eval_platform.repositories.prompt_repository import PromptRepository
from llm_eval_platform.schemas.prompt import PromptCreate, PromptUpdate
from llm_eval_platform.services.common import ServiceBase


class PromptService(ServiceBase):
    def __init__(self, repository: PromptRepository | None = None) -> None:
        self.repository = repository or PromptRepository()

    def create(self, db: Session, payload: PromptCreate):
        prompt = self.repository.create(db, payload.model_dump())
        self._commit(db)
        return self.repository.get_with_versions(db, prompt.id)

    def list(self, db: Session, *, limit: int, offset: int):
        return self.repository.list(db, limit=limit, offset=offset)

    def get(self, db: Session, prompt_id):
        return self._require(self.repository.get_with_versions(db, prompt_id), "Prompt not found.")

    def update(self, db: Session, prompt_id, payload: PromptUpdate):
        prompt = self._require(self.repository.get(db, prompt_id), "Prompt not found.")
        prompt = self.repository.update(db, prompt, payload.model_dump(exclude_none=True))
        self._commit(db)
        return self.repository.get_with_versions(db, prompt.id)

    def delete(self, db: Session, prompt_id) -> None:
        prompt = self._require(self.repository.get(db, prompt_id), "Prompt not found.")
        self.repository.delete(db, prompt)
        self._commit(db)