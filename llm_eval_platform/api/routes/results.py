from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from llm_eval_platform.api.dependencies import get_evaluation_result_service
from llm_eval_platform.api.routes.utils import data_response, list_response
from llm_eval_platform.core.database import get_db
from llm_eval_platform.schemas.result import (
    EvaluationResultCreate,
    EvaluationResultRead,
    EvaluationResultUpdate,
)
from llm_eval_platform.services.evaluation_result_service import EvaluationResultService

router = APIRouter(prefix="/results", tags=["evaluation-results"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_result(
    payload: EvaluationResultCreate,
    db: Session = Depends(get_db),
    service: EvaluationResultService = Depends(get_evaluation_result_service),
):
    return data_response(
        EvaluationResultRead.model_validate(service.create(db, payload)).model_dump(mode="json")
    )


@router.get("", response_model=dict)
def list_results(
    run_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    service: EvaluationResultService = Depends(get_evaluation_result_service),
):
    items, total = service.list(db, limit=limit, offset=offset, run_id=run_id)
    data = [EvaluationResultRead.model_validate(item).model_dump(mode="json") for item in items]
    return list_response(data, limit=limit, offset=offset, total=total)


@router.get("/{result_id}", response_model=dict)
def get_result(
    result_id: UUID,
    db: Session = Depends(get_db),
    service: EvaluationResultService = Depends(get_evaluation_result_service),
):
    return data_response(
        EvaluationResultRead.model_validate(service.get(db, result_id)).model_dump(mode="json")
    )


@router.patch("/{result_id}", response_model=dict)
def update_result(
    result_id: UUID,
    payload: EvaluationResultUpdate,
    db: Session = Depends(get_db),
    service: EvaluationResultService = Depends(get_evaluation_result_service),
):
    return data_response(
        EvaluationResultRead.model_validate(service.update(db, result_id, payload)).model_dump(
            mode="json"
        )
    )


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_result(
    result_id: UUID,
    db: Session = Depends(get_db),
    service: EvaluationResultService = Depends(get_evaluation_result_service),
):
    service.delete(db, result_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)