from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from llm_eval_platform.models.evaluation_result import EvaluationResult
from llm_eval_platform.models.run import Run


class HumanReviewService:
    def get_review_queue(self, db: Session, run_id: UUID, *, limit: int = 50) -> list[dict[str, object]]:
        tenant_id = db.info.get("tenant_id")
        stmt = (
            select(EvaluationResult)
            .join(Run, Run.id == EvaluationResult.run_id)
            .where(EvaluationResult.run_id == run_id)
            .order_by(EvaluationResult.example_index.asc())
            .limit(limit)
        )
        if tenant_id:
            stmt = stmt.where(EvaluationResult.tenant_id == tenant_id)

        results = db.scalars(stmt).all()
        queue: list[dict[str, object]] = []
        for result in results:
            review = (result.result_metadata or {}).get("human_review") or {}
            if review.get("status") in {"approved", "rejected"}:
                continue
            queue.append(
                {
                    "result_id": result.id,
                    "run_id": result.run_id,
                    "example_index": result.example_index,
                    "status": review.get("status", "pending"),
                    "reviewer": review.get("reviewer"),
                    "claimed_at": review.get("claimed_at"),
                }
            )
        return queue

    def claim(self, db: Session, result_id: UUID, reviewer: str) -> dict[str, object]:
        result = db.scalar(select(EvaluationResult).where(EvaluationResult.id == result_id))
        if result is None:
            raise ValueError("Evaluation result not found.")
        meta = dict(result.result_metadata or {})
        review = dict(meta.get("human_review") or {})
        review["status"] = "in_review"
        review["reviewer"] = reviewer
        review["claimed_at"] = datetime.now(timezone.utc).isoformat()
        meta["human_review"] = review
        result.result_metadata = meta
        db.add(result)
        db.commit()
        db.refresh(result)
        return {"result_id": result.id, "human_review": review}

    def submit(
        self,
        db: Session,
        result_id: UUID,
        reviewer: str,
        decision: str,
        notes: str | None,
        score_override: float | None,
    ) -> dict[str, object]:
        result = db.scalar(select(EvaluationResult).where(EvaluationResult.id == result_id))
        if result is None:
            raise ValueError("Evaluation result not found.")
        meta = dict(result.result_metadata or {})
        review = dict(meta.get("human_review") or {})
        review.update(
            {
                "status": decision,
                "reviewer": reviewer,
                "notes": notes,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "score_override": score_override,
            }
        )
        meta["human_review"] = review
        result.result_metadata = meta
        if score_override is not None:
            result.score = score_override
        db.add(result)
        db.commit()
        db.refresh(result)
        return {"result_id": result.id, "human_review": review, "score": result.score}