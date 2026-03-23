from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from llm_eval_platform.api.dependencies import get_model_config_service
from llm_eval_platform.api.routes.utils import data_response, list_response
from llm_eval_platform.core.database import get_db
from llm_eval_platform.schemas.model_config import ModelConfigCreate, ModelConfigRead, ModelConfigUpdate
from llm_eval_platform.services.model_config_service import ModelConfigService

router = APIRouter(prefix="/models", tags=["model-configs"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_model_config(
    payload: ModelConfigCreate,
    db: Session = Depends(get_db),
    service: ModelConfigService = Depends(get_model_config_service),
):
    return data_response(
        ModelConfigRead.model_validate(service.create(db, payload)).model_dump(mode="json")
    )


@router.get("", response_model=dict)
def list_model_configs(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    service: ModelConfigService = Depends(get_model_config_service),
):
    items, total = service.list(db, limit=limit, offset=offset)
    data = [ModelConfigRead.model_validate(item).model_dump(mode="json") for item in items]
    return list_response(data, limit=limit, offset=offset, total=total)


@router.get("/{model_config_id}", response_model=dict)
def get_model_config(
    model_config_id: UUID,
    db: Session = Depends(get_db),
    service: ModelConfigService = Depends(get_model_config_service),
):
    return data_response(
        ModelConfigRead.model_validate(service.get(db, model_config_id)).model_dump(mode="json")
    )


@router.patch("/{model_config_id}", response_model=dict)
def update_model_config(
    model_config_id: UUID,
    payload: ModelConfigUpdate,
    db: Session = Depends(get_db),
    service: ModelConfigService = Depends(get_model_config_service),
):
    return data_response(
        ModelConfigRead.model_validate(service.update(db, model_config_id, payload)).model_dump(
            mode="json"
        )
    )


@router.delete("/{model_config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_config(
    model_config_id: UUID,
    db: Session = Depends(get_db),
    service: ModelConfigService = Depends(get_model_config_service),
):
    service.delete(db, model_config_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)