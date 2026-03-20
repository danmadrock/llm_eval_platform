from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    data: list
    pagination: dict[str, int]


class DatasetBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    task_type: str = Field(min_length=1, max_length=100)


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    task_type: str | None = Field(default=None, min_length=1, max_length=100)


class DatasetVersionCreate(BaseModel):
    object_uri: str = Field(min_length=1, max_length=1024)
    example_count: int = Field(ge=0)


class DatasetVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    version: int
    object_uri: str
    example_count: int
    created_at: datetime
    updated_at: datetime


class DatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    task_type: str
    created_at: datetime
    updated_at: datetime
    versions: list[DatasetVersionRead] = []