from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, update
from sqlalchemy.orm import Session

from llm_eval_platform.models.run import Run


class RunProgressTracker:
    def mark_running(self, db: Session, run_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        db.execute(
            update(Run)
            .where(Run.id == run_id)
            .values(
                status=case((Run.status == "queued", "running"), else_=Run.status),
                started_at=case((Run.started_at.is_(None), now), else_=Run.started_at),
            )
        )
        db.flush()

    def record_result(self, db: Session, run_id: UUID, *, succeeded: bool, error_message: str | None = None,) -> None:
        now = datetime.now(timezone.utc)
        failed_increment = 0 if succeeded else 1
        completed_increment = 1 if succeeded else 0
        next_failed = Run.failed_examples + failed_increment
        next_processed = Run.processed_examples + 1
        terminal_status = case((next_failed > 0, "failed"), else_="completed")
        
        db.execute(
            update(Run)
            .where(Run.id == run_id)
            .values(
                processed_examples=next_processed,
                completed_examples=Run.completed_examples + completed_increment,
                failed_examples=next_failed,
                error_message=error_message if error_message is not None else Run.error_message,
                status=case(
                    (Run.total_examples == 0, "completed"),
                    (next_processed >= Run.total_examples, terminal_status),
                    else_="running",
                ),
                completed_at=case(
                    (Run.total_examples == 0, now),
                    (next_processed >= Run.total_examples, now),
                    else_=Run.completed_at,
                ),
            )
        )
        db.flush()