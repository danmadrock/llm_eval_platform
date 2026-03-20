from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PromptBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class PromptVersionCreate(BaseModel):
    template: str = Field(min_length=1)


class PromptVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prompt_id: UUID
    version: int
    template: str
    created_at: datetime
    updated_at: datetime


class PromptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    versions: list[PromptVersionRead] = []