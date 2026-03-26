from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from llm_eval_platform.api.routes.utils import data_response, list_response
from llm_eval_platform.core.database import get_db
from llm_eval_platform.schemas.phase5 import HumanReviewClaimRequest, HumanReviewSubmitRequest
from llm_eval_platform.services.human_review.review_service import HumanReviewService

router = APIRouter(prefix="/human-review", tags=["human-review"])


def get_review_service() -> HumanReviewService:
    return HumanReviewService()


@router.get("/runs/{run_id}/queue", response_model=dict)
def get_review_queue(
    run_id: UUID,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    service: HumanReviewService = Depends(get_review_service),
):
    queue = service.get_review_queue(db, run_id, limit=limit)
    return list_response(queue, limit=limit, offset=0, total=len(queue))


@router.post("/results/{result_id}/claim", response_model=dict)
def claim_review(
    result_id: UUID,
    payload: HumanReviewClaimRequest,
    db: Session = Depends(get_db),
    service: HumanReviewService = Depends(get_review_service),
):
    return data_response(service.claim(db, result_id, reviewer=payload.reviewer))


@router.post("/results/{result_id}/submit", response_model=dict)
def submit_review(
    result_id: UUID,
    payload: HumanReviewSubmitRequest,
    db: Session = Depends(get_db),
    service: HumanReviewService = Depends(get_review_service),
):
    return data_response(
        service.submit(
            db,
            result_id,
            reviewer=payload.reviewer,
            decision=payload.decision,
            notes=payload.notes,
            score_override=payload.score_override,
        )
    )