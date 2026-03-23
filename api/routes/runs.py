from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from llm_eval_platform.api.dependencies import get_run_service
from llm_eval_platform.api.routes.utils import data_response, list_response
from llm_eval_platform.core.database import get_db
from llm_eval_platform.schemas.run import RunCreate, RunRead, RunUpdate
from llm_eval_platform.services.runs.run_service import RunService

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_run(
    payload: RunCreate,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
):
    return data_response(
        RunRead.model_validate(service.create(db, payload)).model_dump(mode="json")
    )


@router.get("", response_model=dict)
def list_runs(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
):
    items, total = service.list(db, limit=limit, offset=offset)
    data = [RunRead.model_validate(item).model_dump(mode="json") for item in items]
    return list_response(data, limit=limit, offset=offset, total=total)


@router.get("/{run_id}", response_model=dict)
def get_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
):
    return data_response(RunRead.model_validate(service.get(db, run_id)).model_dump(mode="json"))


@router.patch("/{run_id}", response_model=dict)
def update_run(
    run_id: UUID,
    payload: RunUpdate,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
):
    return data_response(
        RunRead.model_validate(service.update(db, run_id, payload)).model_dump(mode="json")
    )


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    service: RunService = Depends(get_run_service),
):
    service.delete(db, run_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)