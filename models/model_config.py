from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database_models import TimestampedModel, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.run import Run


class ModelConfig(UUIDPrimaryKeyMixin, TimestampedModel):
    __tablename__ = "model_configs"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(100), index=True)
    model_name: Mapped[str] = mapped_column(String(255), index=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    runs: Mapped[list[Run]] = relationship(back_populates="model_config")