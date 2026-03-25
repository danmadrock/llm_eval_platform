from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from llm_eval_platform.api.routes.utils import data_response
from llm_eval_platform.core.database import get_db
from llm_eval_platform.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service() -> DashboardService:
    return DashboardService()


@router.get("/overview", response_model=dict)
def get_overview(
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
):
    return data_response(service.get_overview(db))


@router.get("/run-trends", response_model=dict)
def get_run_trends(
    days: int = Query(default=14, ge=1, le=90),
    db: Session = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
):
    return data_response(service.get_run_trends(db, days=days))