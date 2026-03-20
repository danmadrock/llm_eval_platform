from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database_models import TimestampedModel, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.run import Run


class Prompt(UUIDPrimaryKeyMixin, TimestampedModel):
    __tablename__ = "prompts"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    versions: Mapped[list[PromptVersion]] = relationship(
        back_populates="prompt", cascade="all, delete-orphan", order_by="PromptVersion.version"
    )


class PromptVersion(UUIDPrimaryKeyMixin, TimestampedModel):
    __tablename__ = "prompt_versions"
    __table_args__ = (UniqueConstraint("prompt_id", "version"),)

    prompt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    template: Mapped[str] = mapped_column(Text())

    prompt: Mapped[Prompt] = relationship(back_populates="versions")
    runs: Mapped[list[Run]] = relationship(back_populates="prompt_version")