from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Generic, Protocol, TypeVar, cast, runtime_checkable

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from llm_eval_platform.core.exceptions import ConflictError

@runtime_checkable
class RepositoryModel(Protocol):
    id: Any


ModelT = TypeVar("ModelT", bound=RepositoryModel)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT]):
        self.model = model

    @staticmethod
    def _flush_or_raise(db: Session) -> None:
        try:
            db.flush()
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("Resource violates a uniqueness or integrity constraint.") from exc

    @staticmethod
    def _tenant_for(db: Session) -> str | None:
        return cast(str | None, db.info.get("tenant_id"))

    def _scope_payload(self, db: Session, payload: Mapping[str, Any]) -> dict[str, Any]:
        scoped = dict(payload)
        tenant_id = self._tenant_for(db)
        if tenant_id and hasattr(self.model, "tenant_id"):
            scoped.setdefault("tenant_id", tenant_id)
        return scoped

    def _tenant_filter(self, db: Session, stmt: Select[Any]) -> Select[Any]:
        tenant_id = self._tenant_for(db)
        if tenant_id and hasattr(self.model, "tenant_id"):
            return stmt.where(getattr(self.model, "tenant_id") == tenant_id)
        return stmt

    def create(self, db: Session, payload: Mapping[str, Any]) -> ModelT:
        instance = self.model(**self._scope_payload(db, payload))
        db.add(instance)
        self._flush_or_raise(db)
        db.refresh(instance)
        return instance

    def get(self, db: Session, entity_id: Any) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == entity_id)
        stmt = self._tenant_filter(db, stmt)
        return cast(ModelT | None, db.scalar(stmt))

    def list(self, db: Session, *, limit: int, offset: int) -> tuple[list[ModelT], int]:
        stmt = select(self.model).offset(offset).limit(limit)
        stmt = self._tenant_filter(db, stmt)
        items = list(cast(list[ModelT], db.scalars(stmt).all()))
        total_stmt = self._tenant_filter(db, select(func.count()).select_from(self.model))
        total = int(db.scalar(total_stmt) or 0)
        return items, total

    def update(self, db: Session, instance: ModelT, payload: Mapping[str, Any]) -> ModelT:
        for key, value in payload.items():
            setattr(instance, key, value)
        db.add(instance)
        self._flush_or_raise(db)
        db.refresh(instance)
        return instance

    def delete(self, db: Session, instance: ModelT) -> None:
        db.delete(instance)
        self._flush_or_raise(db)