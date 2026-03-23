from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from llm_eval_platform.models.prompt import Prompt, PromptVersion
from llm_eval_platform.repositories.base_repository import BaseRepository


class PromptRepository(BaseRepository[Prompt]):
    def __init__(self) -> None:
        super().__init__(Prompt)

    def get_with_versions(self, db: Session, prompt_id):
        stmt = select(Prompt).options(selectinload(Prompt.versions)).where(Prompt.id == prompt_id)
        return db.scalar(stmt)

    def create_version(self, db: Session, prompt_id, *, template: str) -> PromptVersion:
        next_version = (
            db.scalar(
                select(func.max(PromptVersion.version)).where(PromptVersion.prompt_id == prompt_id)
            )
            or 0
        ) + 1
        prompt_version = PromptVersion(prompt_id=prompt_id, version=next_version, template=template)
        db.add(prompt_version)
        db.flush()
        db.refresh(prompt_version)
        return prompt_version

    def list_versions(self, db: Session, prompt_id):
        return db.scalars(
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version)
        ).all()

    def get_version(self, db: Session, version_id):
        return db.get(PromptVersion, version_id)