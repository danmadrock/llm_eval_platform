from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import ConflictError, NotFoundError


class ServiceBase:
    @staticmethod
    def _commit(db: Session) -> None:
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("Resource violates a uniqueness or integrity constraint.") from exc

    @staticmethod
    def _require(instance, message: str):
        if instance is None:
            raise NotFoundError(message)
        return instance