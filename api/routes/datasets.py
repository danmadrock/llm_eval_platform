from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from api.dependencies import get_dataset_service, get_dataset_version_service
from api.routes.utils import data_response, list_response
from core.database import get_db
from schemas.dataset import (
    DatasetCreate,
    DatasetRead,
    DatasetUpdate,
    DatasetVersionCreate,
    DatasetVersionRead,
)
from services.datasets.dataset_service import DatasetService
from services.datasets.dataset_version_service import DatasetVersionService


router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: DatasetCreate,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    return data_response(
        DatasetRead.model_validate(service.create(db, payload)).model_dump(mode="json")
    )


@router.get("", response_model=dict)
def list_datasets(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    items, total = service.list(db, limit=limit, offset=offset)
    data = [DatasetRead.model_validate(item).model_dump(mode="json") for item in items]
    return list_response(data, limit=limit, offset=offset, total=total)


@router.get("/{dataset_id}", response_model=dict)
def get_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    return data_response(
        DatasetRead.model_validate(service.get(db, dataset_id)).model_dump(mode="json")
    )


@router.patch("/{dataset_id}", response_model=dict)
def update_dataset(
    dataset_id: UUID,
    payload: DatasetUpdate,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    return data_response(
        DatasetRead.model_validate(service.update(db, dataset_id, payload)).model_dump(mode="json")
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service),
):
    service.delete(db, dataset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{dataset_id}/versions", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_dataset_version(
    dataset_id: UUID,
    payload: DatasetVersionCreate,
    db: Session = Depends(get_db),
    service: DatasetVersionService = Depends(get_dataset_version_service),
):
    return data_response(
        DatasetVersionRead.model_validate(service.create(db, dataset_id, payload)).model_dump(
            mode="json"
        )
    )


@router.get("/{dataset_id}/versions", response_model=dict)
def list_dataset_versions(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    service: DatasetVersionService = Depends(get_dataset_version_service),
):
    data = [
        DatasetVersionRead.model_validate(item).model_dump(mode="json")
        for item in service.list(db, dataset_id)
    ]
    return data_response(data)