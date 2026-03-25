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
        return db.scalar(self._tenant_filter(db, stmt))

    def create_version(self, db: Session, prompt_id, *, template: str) -> PromptVersion:
        tenant_id = db.info.get("tenant_id")
        stmt = select(func.max(PromptVersion.version)).where(PromptVersion.prompt_id == prompt_id)
        if tenant_id:
            stmt = stmt.where(PromptVersion.tenant_id == tenant_id)
        next_version = (db.scalar(stmt) or 0) + 1
        prompt_version = PromptVersion(prompt_id=prompt_id, version=next_version, template=template, tenant_id=tenant_id)
        db.add(prompt_version)
        db.flush()
        db.refresh(prompt_version)
        return prompt_version

    def list_versions(self, db: Session, prompt_id):
        stmt = select(PromptVersion).where(PromptVersion.prompt_id == prompt_id).order_by(PromptVersion.version)
        tenant_id = db.info.get("tenant_id")
        if tenant_id:
            stmt = stmt.where(PromptVersion.tenant_id == tenant_id)
        return db.scalars(stmt).all()

    def get_version(self, db: Session, version_id):
        stmt = select(PromptVersion).where(PromptVersion.id == version_id)
        tenant_id = db.info.get("tenant_id")
        if tenant_id:
            stmt = stmt.where(PromptVersion.tenant_id == tenant_id)
        return db.scalar(stmt)