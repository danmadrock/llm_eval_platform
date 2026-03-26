from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from llm_eval_platform.api.routes.utils import data_response
from llm_eval_platform.core.database import get_db
from llm_eval_platform.schemas.comparison import QualityCostFrontierRead
from llm_eval_platform.services.phase5.comparison_service import ComparisonService

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


def get_comparison_service() -> ComparisonService:
    return ComparisonService()


@router.get("/experiments/{experiment_id}/quality-cost-frontier", response_model=dict)
def get_quality_cost_frontier(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    service: ComparisonService = Depends(get_comparison_service),
):
    payload = service.get_quality_cost_frontier(db, experiment_id)
    return data_response(QualityCostFrontierRead.model_validate(payload).model_dump(mode="json"))
