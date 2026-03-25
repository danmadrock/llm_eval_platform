from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from llm_eval_platform.models.evaluation_result import EvaluationResult
from llm_eval_platform.models.run import Run


class DashboardService:
    def get_overview(self, db: Session) -> dict:
        tenant_id = db.info.get("tenant_id")
        runs_stmt = select(func.count()).select_from(Run)
        active_stmt = select(func.count()).select_from(Run).where(Run.status.in_(["created", "queued", "running"]))
        result_stmt = select(func.count()).select_from(EvaluationResult)
        avg_score_stmt = select(func.avg(EvaluationResult.score)).where(EvaluationResult.score.is_not(None))
        if tenant_id:
            runs_stmt = runs_stmt.where(Run.tenant_id == tenant_id)
            active_stmt = active_stmt.where(Run.tenant_id == tenant_id)
            result_stmt = result_stmt.where(EvaluationResult.tenant_id == tenant_id)
            avg_score_stmt = avg_score_stmt.where(EvaluationResult.tenant_id == tenant_id)
        return {
            "total_runs": db.scalar(runs_stmt) or 0,
            "active_runs": db.scalar(active_stmt) or 0,
            "total_results": db.scalar(result_stmt) or 0,
            "average_score": float(db.scalar(avg_score_stmt) or 0.0),
        }

    def get_run_trends(self, db: Session, *, days: int = 14) -> dict:
        tenant_id = db.info.get("tenant_id")
        start = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(
                func.date(Run.created_at).label("day"),
                func.count().label("run_count"),
                func.sum(case((Run.status == "completed", 1), else_=0)).label("completed_count"),
            )
            .where(Run.created_at >= start)
            .group_by(func.date(Run.created_at))
            .order_by(func.date(Run.created_at))
        )
        if tenant_id:
            stmt = stmt.where(Run.tenant_id == tenant_id)
        series = [
            {"day": str(day), "run_count": int(run_count), "completed_count": int(completed_count or 0)}
            for day, run_count, completed_count in db.execute(stmt).all()
        ]
        return {"window_days": days, "series": series}
