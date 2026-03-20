from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    experiment_id: UUID
    dataset_version_id: UUID
    prompt_version_id: UUID
    model_config_id: UUID
    status: str = Field(default="created", min_length=1, max_length=50)
    parameters: dict = Field(default_factory=dict)
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str | None = Field(default=None, min_length=1, max_length=50)
    parameters: dict | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    experiment_id: UUID
    dataset_version_id: UUID
    prompt_version_id: UUID
    model_config_id: UUID
    status: str
    parameters: dict
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime