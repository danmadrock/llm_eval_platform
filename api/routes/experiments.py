from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from api.dependencies import get_experiment_service
from api.routes.utils import data_response, list_response
from core.database import get_db
from schemas.experiment import ExperimentCreate, ExperimentRead, ExperimentUpdate
from services.experiments.experiment_service import ExperimentService

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: ExperimentCreate,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
):
    return data_response(
        ExperimentRead.model_validate(service.create(db, payload)).model_dump(mode="json")
    )


@router.get("", response_model=dict)
def list_experiments(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
):
    items, total = service.list(db, limit=limit, offset=offset)
    data = [ExperimentRead.model_validate(item).model_dump(mode="json") for item in items]
    return list_response(data, limit=limit, offset=offset, total=total)


@router.get("/{experiment_id}", response_model=dict)
def get_experiment(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
):
    return data_response(
        ExperimentRead.model_validate(service.get(db, experiment_id)).model_dump(mode="json")
    )


@router.patch("/{experiment_id}", response_model=dict)
def update_experiment(
    experiment_id: UUID,
    payload: ExperimentUpdate,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
):
    return data_response(
        ExperimentRead.model_validate(service.update(db, experiment_id, payload)).model_dump(
            mode="json"
        )
    )


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    service: ExperimentService = Depends(get_experiment_service),
):
    service.delete(db, experiment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)