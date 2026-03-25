from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_eval_platform.models.database_models import TenantScopedMixin, TimestampedModel, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from llm_eval_platform.models.run import Run


class Experiment(UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampedModel):
    __tablename__ = "experiments"
    __table_args__ = (UniqueConstraint("tenant_id", "name"),)

    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    runs: Mapped[list[Run]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan", order_by="Run.created_at"
    )