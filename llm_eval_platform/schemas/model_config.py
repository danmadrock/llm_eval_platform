from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModelConfigBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=100)
    model_name: str = Field(min_length=1, max_length=255)
    parameters: dict = Field(default_factory=dict)
    description: str | None = None


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    model_name: str | None = Field(default=None, min_length=1, max_length=255)
    parameters: dict | None = None
    description: str | None = None


class ModelConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    name: str
    provider: str
    model_name: str
    parameters: dict
    description: str | None
    created_at: datetime
    updated_at: datetime