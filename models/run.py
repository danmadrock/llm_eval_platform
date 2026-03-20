from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database_models import TimestampedModel, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.dataset import DatasetVersion
    from models.evaluation_result import EvaluationResult
    from models.experiment import Experiment
    from models.model_config import ModelConfig
    from models.prompt import PromptVersion


class Run(UUIDPrimaryKeyMixin, TimestampedModel):
    __tablename__ = "runs"

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), index=True
    )
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dataset_versions.id"), index=True
    )
    prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompt_versions.id"), index=True
    )
    model_config_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_configs.id"), index=True)

    status: Mapped[str] = mapped_column(String(50), default="created", index=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    experiment: Mapped[Experiment] = relationship(back_populates="runs")
    dataset_version: Mapped[DatasetVersion] = relationship(back_populates="runs")
    prompt_version: Mapped[PromptVersion] = relationship(back_populates="runs")
    model_config: Mapped[ModelConfig] = relationship(back_populates="runs")
    evaluation_results: Mapped[list[EvaluationResult]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EvaluationResult.example_index",
    )