from __future__ import annotations

from sqlalchemy.orm import Session

from models.run import Run
from repositories.base_repository import BaseRepository


class RunRepository(BaseRepository[Run]):
    def __init__(self) -> None:
        super().__init__(Run)

    def get_for_update(self, db: Session, run_id):
        return db.get(Run, run_id)