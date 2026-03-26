from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from llm_eval_platform.api.routes.utils import data_response
from llm_eval_platform.core.database import get_db
from llm_eval_platform.schemas.phase5 import OptimizationHookRead
from llm_eval_platform.services.prompt_optimization.hook_service import PromptOptimizationHookService

router = APIRouter(prefix="/optimization", tags=["optimization"])


def get_hook_service() -> PromptOptimizationHookService:
    return PromptOptimizationHookService()


@router.post("/runs/{run_id}/hook", response_model=dict)
def build_run_optimization_hook(
    run_id: UUID,
    db: Session = Depends(get_db),
    service: PromptOptimizationHookService = Depends(get_hook_service),
):
    payload = service.build_hook_payload(db, run_id)
    return data_response(OptimizationHookRead.model_validate(payload).model_dump(mode="json"))
