from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from llm_eval_platform.models.database_models import TenantScopedMixin, TimestampedModel, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from llm_eval_platform.models.run import Run


class Dataset(UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampedModel):
    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("tenant_id", "name"),)

    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    task_type: Mapped[str] = mapped_column(String(100), index=True)

    versions: Mapped[list[DatasetVersion]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan", order_by="DatasetVersion.version"
    )


class DatasetVersion(UUIDPrimaryKeyMixin, TenantScopedMixin, TimestampedModel):
    __tablename__ = "dataset_versions"
    __table_args__ = (UniqueConstraint("tenant_id", "dataset_id", "version"),)

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    object_uri: Mapped[str] = mapped_column(String(1024))
    example_count: Mapped[int] = mapped_column(Integer)

    dataset: Mapped[Dataset] = relationship(back_populates="versions")
    runs: Mapped[list[Run]] = relationship(back_populates="dataset_version")