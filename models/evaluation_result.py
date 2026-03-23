from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_eval_platform.models.database_models import TimestampedModel, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from llm_eval_platform.models.run import Run


class EvaluationResult(UUIDPrimaryKeyMixin, TimestampedModel):
    __tablename__ = "evaluation_results"
    __table_args__ = (UniqueConstraint("run_id", "example_index"),)

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    example_index: Mapped[int] = mapped_column(Integer)
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actual_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    result_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)

    run: Mapped[Run] = relationship(back_populates="evaluation_results")