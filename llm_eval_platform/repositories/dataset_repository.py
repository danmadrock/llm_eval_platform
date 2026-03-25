from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from llm_eval_platform.models.dataset import Dataset, DatasetVersion
from llm_eval_platform.repositories.base_repository import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    def __init__(self) -> None:
        super().__init__(Dataset)

    def get_with_versions(self, db: Session, dataset_id):
        stmt = select(Dataset).options(selectinload(Dataset.versions)).where(Dataset.id == dataset_id)
        return db.scalar(self._tenant_filter(db, stmt))

    def create_version(self, db: Session, dataset_id, *, object_uri: str, example_count: int) -> DatasetVersion:
        tenant_id = db.info.get("tenant_id")
        version_stmt = select(func.max(DatasetVersion.version)).where(DatasetVersion.dataset_id == dataset_id)
        if tenant_id:
            version_stmt = version_stmt.where(DatasetVersion.tenant_id == tenant_id)
        next_version = (db.scalar(version_stmt) or 0) + 1
        dataset_version = DatasetVersion(
            dataset_id=dataset_id,
            version=next_version,
            object_uri=object_uri,
            example_count=example_count,
            tenant_id=tenant_id,
        )
        db.add(dataset_version)
        db.flush()
        db.refresh(dataset_version)
        return dataset_version

    def list_versions(self, db: Session, dataset_id):
        stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version)
        tenant_id = db.info.get("tenant_id")
        if tenant_id:
            stmt = stmt.where(DatasetVersion.tenant_id == tenant_id)
        return db.scalars(stmt).all()

    def get_version(self, db: Session, version_id):
        stmt = select(DatasetVersion).where(DatasetVersion.id == version_id)
        tenant_id = db.info.get("tenant_id")
        if tenant_id:
            stmt = stmt.where(DatasetVersion.tenant_id == tenant_id)
        return db.scalar(stmt)