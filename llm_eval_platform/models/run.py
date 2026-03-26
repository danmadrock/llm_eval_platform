from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_eval_platform.models.database_models import TenantScopedMixin, TimestampedModel, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from llm_eval_platform.models.dataset import DatasetVersion
    from llm_eval_platform.models.evaluation_result import EvaluationResult
    from llm_eval_platform.models.experiment import Experiment
    from llm_eval_platform.models.model_config import ModelConfig
    from llm_eval_platform.models.prompt import PromptVersion
    from llm_eval_platform.models.run_metric import RunMetric


class Run(UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampedModel):
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
    baseline_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("runs.id"), index=True, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="created", index=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    total_examples: Mapped[int] = mapped_column(Integer, default=0)
    processed_examples: Mapped[int] = mapped_column(Integer, default=0)
    completed_examples: Mapped[int] = mapped_column(Integer, default=0)
    failed_examples: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    result_artifact_uri: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    regression_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    regression_summary: Mapped[dict] = mapped_column(JSON, default=dict)
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
    metrics: Mapped[list[RunMetric]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RunMetric.metric_name",
    )