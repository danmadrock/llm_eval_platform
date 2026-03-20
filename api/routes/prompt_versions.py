from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.dependencies import get_prompt_version_service
from api.routes.utils import data_response
from core.database import get_db
from schemas.prompt import PromptVersionCreate, PromptVersionRead
from services.prompts.prompt_version_service import PromptVersionService

router = APIRouter(prefix="/prompts", tags=["prompt-versions"])


@router.post("/{prompt_id}/versions", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_prompt_version(
    prompt_id: UUID,
    payload: PromptVersionCreate,
    db: Session = Depends(get_db),
    service: PromptVersionService = Depends(get_prompt_version_service),
):
    return data_response(
        PromptVersionRead.model_validate(service.create(db, prompt_id, payload)).model_dump(
            mode="json"
        )
    )


@router.get("/{prompt_id}/versions", response_model=dict)
def list_prompt_versions(
    prompt_id: UUID,
    db: Session = Depends(get_db),
    service: PromptVersionService = Depends(get_prompt_version_service),
):
    data = [
        PromptVersionRead.model_validate(item).model_dump(mode="json")
        for item in service.list(db, prompt_id)
    ]
    return data_response(data)