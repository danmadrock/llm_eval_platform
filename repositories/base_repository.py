from __future__ import annotations

from collections.abc import Mapping
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import ConflictError

ModelT = TypeVar("ModelT")


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

    def create(self, db: Session, payload: Mapping) -> ModelT:
        instance = self.model(**dict(payload))
        db.add(instance)
        self._flush_or_raise(db)
        db.refresh(instance)
        return instance

    def get(self, db: Session, entity_id) -> ModelT | None:
        return db.get(self.model, entity_id)

    def list(self, db: Session, *, limit: int, offset: int):
        items = db.scalars(select(self.model).offset(offset).limit(limit)).all()
        total = db.scalar(select(func.count()).select_from(self.model)) or 0
        return items, total

    def update(self, db: Session, instance: ModelT, payload: Mapping) -> ModelT:
        for key, value in payload.items():
            setattr(instance, key, value)
        db.add(instance)
        self._flush_or_raise(db)
        db.refresh(instance)
        return instance

    def delete(self, db: Session, instance: ModelT) -> None:
        db.delete(instance)
        self._flush_or_raise(db)