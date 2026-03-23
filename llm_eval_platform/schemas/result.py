from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluationResultCreate(BaseModel):
    run_id: UUID
    example_index: int = Field(ge=0)
    input_payload: dict = Field(default_factory=dict)
    expected_output: dict | None = None
    actual_output: dict | None = None
    score: float | None = None
    status: str = Field(default="pending", min_length=1, max_length=50)
    metadata: dict = Field(default_factory=dict, serialization_alias="metadata")
    error_message: str | None = None

    def model_dump(self, *args, **kwargs):  # type: ignore[override]
        data = super().model_dump(*args, **kwargs)
        data["result_metadata"] = data.pop("metadata")
        return data


class EvaluationResultUpdate(BaseModel):
    input_payload: dict | None = None
    expected_output: dict | None = None
    actual_output: dict | None = None
    score: float | None = None
    status: str | None = Field(default=None, min_length=1, max_length=50)
    metadata: dict | None = Field(default=None, serialization_alias="metadata")
    error_message: str | None = None

    def model_dump(self, *args, **kwargs):  # type: ignore[override]
        data = super().model_dump(*args, **kwargs)
        if "metadata" in data:
            data["result_metadata"] = data.pop("metadata")
        return data


class EvaluationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    example_index: int
    input_payload: dict
    expected_output: dict | None
    actual_output: dict | None
    score: float | None
    status: str
    result_metadata: dict = Field(serialization_alias="metadata")
    error_message: str | None
    created_at: datetime
    updated_at: datetime