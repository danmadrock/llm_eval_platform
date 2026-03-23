from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from llm_eval_platform.api.dependencies import get_prompt_service
from llm_eval_platform.api.routes.utils import data_response, list_response
from llm_eval_platform.core.database import get_db
from llm_eval_platform.schemas.prompt import PromptCreate, PromptRead, PromptUpdate
from llm_eval_platform.services.prompts.prompt_service import PromptService

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_prompt(
    payload: PromptCreate,
    db: Session = Depends(get_db),
    service: PromptService = Depends(get_prompt_service),
):
    return data_response(
        PromptRead.model_validate(service.create(db, payload)).model_dump(mode="json")
    )


@router.get("", response_model=dict)
def list_prompts(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    service: PromptService = Depends(get_prompt_service),
):
    items, total = service.list(db, limit=limit, offset=offset)
    data = [PromptRead.model_validate(item).model_dump(mode="json") for item in items]
    return list_response(data, limit=limit, offset=offset, total=total)


@router.get("/{prompt_id}", response_model=dict)
def get_prompt(
    prompt_id: UUID,
    db: Session = Depends(get_db),
    service: PromptService = Depends(get_prompt_service),
):
    return data_response(
        PromptRead.model_validate(service.get(db, prompt_id)).model_dump(mode="json")
    )


@router.patch("/{prompt_id}", response_model=dict)
def update_prompt(
    prompt_id: UUID,
    payload: PromptUpdate,
    db: Session = Depends(get_db),
    service: PromptService = Depends(get_prompt_service),
):
    return data_response(
        PromptRead.model_validate(service.update(db, prompt_id, payload)).model_dump(mode="json")
    )


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    prompt_id: UUID,
    db: Session = Depends(get_db),
    service: PromptService = Depends(get_prompt_service),
):
    service.delete(db, prompt_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)