from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from llm_eval_platform.core.config import get_settings
from llm_eval_platform.core.exceptions import ConflictError
from llm_eval_platform.repositories.dataset_repository import DatasetRepository
from llm_eval_platform.repositories.experiment_repository import ExperimentRepository
from llm_eval_platform.repositories.model_repository import ModelRepository
from llm_eval_platform.repositories.prompt_repository import PromptRepository
from llm_eval_platform.repositories.run_repository import RunRepository
from llm_eval_platform.schemas.run import RunCreate, RunUpdate
from llm_eval_platform.services.common import ServiceBase
from llm_eval_platform.services.run_orchestration.orchestrator import RunOrchestrator
from llm_eval_platform.services.runs.regression_service import RegressionService
from llm_eval_platform.services.runs.run_aggregator import RunAggregator
from llm_eval_platform.storage.artifact_storage import ArtifactStorage


class RunService(ServiceBase):
    def __init__(
        self,
        repository: RunRepository | None = None,
        experiment_repository: ExperimentRepository | None = None,
        dataset_repository: DatasetRepository | None = None,
        prompt_repository: PromptRepository | None = None,
        model_repository: ModelRepository | None = None,
        orchestrator: RunOrchestrator | None = None,
        run_aggregator: RunAggregator | None = None,
        regression_service: RegressionService | None = None,
        artifact_storage: ArtifactStorage | None = None,
    ) -> None:
        self.repository = repository or RunRepository()
        self.experiment_repository = experiment_repository or ExperimentRepository()
        self.dataset_repository = dataset_repository or DatasetRepository()
        self.prompt_repository = prompt_repository or PromptRepository()
        self.model_repository = model_repository or ModelRepository()
        self.orchestrator = orchestrator or RunOrchestrator()
        self.run_aggregator = run_aggregator or RunAggregator()
        self.regression_service = regression_service or RegressionService()
        self.artifact_storage = artifact_storage or ArtifactStorage()

    def create(self, db: Session, payload: RunCreate):
        self._require(
            self.experiment_repository.get(db, payload.experiment_id), "Experiment not found."
        )
        self._require(
            self.dataset_repository.get_version(db, payload.dataset_version_id),
            "Dataset version not found.",
        )
        self._require(
            self.prompt_repository.get_version(db, payload.prompt_version_id),
            "Prompt version not found.",
        )
        self._require(
            self.model_repository.get(db, payload.model_config_id), "Model config not found."
        )
        if payload.baseline_run_id is not None:
            self._require(self.repository.get(db, payload.baseline_run_id), "Baseline run not found.")

        self._enforce_daily_quota(db)
        run = self.repository.create(db, payload.model_dump())
        self._commit(db)
        return run

    def list(self, db: Session, *, limit: int, offset: int):
        return self.repository.list(db, limit=limit, offset=offset)

    def get(self, db: Session, run_id):
        return self._require(self.repository.get(db, run_id), "Run not found.")

    def update(self, db: Session, run_id, payload: RunUpdate):
        run = self._require(self.repository.get_for_update(db, run_id), "Run not found.")
        run = self.repository.update(db, run, payload.model_dump(exclude_none=True))
        self._commit(db)
        return run

    def enqueue(self, db: Session, run_id):
        return self.orchestrator.enqueue_run(db, run_id)
    
    def delete(self, db: Session, run_id) -> None:
        run = self._require(self.repository.get(db, run_id), "Run not found.")
        self.repository.delete(db, run)
        self._commit(db)

    def get_analytics(self, db: Session, run_id):
        run = self._require(self.repository.get(db, run_id), "Run not found.")
        self.run_aggregator.update_summary(db, run_id)
        analytics = self.run_aggregator.get_analytics(db, run_id)
        self._persist_analytics_artifact(db, run, analytics)
        if run.baseline_run_id:
            baseline_analytics = self.run_aggregator.get_analytics(db, run.baseline_run_id)
            regression = self.regression_service.evaluate(baseline_analytics, analytics)
            run.regression_status = regression["status"]
            run.regression_summary = regression
            db.add(run)
        self._commit(db)
        return analytics

    def get_regression_report(self, db: Session, run_id):
        run = self._require(self.repository.get(db, run_id), "Run not found.")
        if not run.baseline_run_id:
            raise ConflictError("Run does not define a baseline for regression detection.")
        baseline = self._require(self.repository.get(db, run.baseline_run_id), "Baseline run not found.")
        candidate_analytics = self.run_aggregator.get_analytics(db, run.id)
        baseline_analytics = self.run_aggregator.get_analytics(db, baseline.id)
        regression = self.regression_service.evaluate(baseline_analytics, candidate_analytics)
        run.regression_status = regression["status"]
        run.regression_summary = regression
        db.add(run)
        self._commit(db)
        return {
            "candidate_run_id": run.id,
            "baseline_run_id": baseline.id,
            **regression,
        }

    def _enforce_daily_quota(self, db: Session) -> None:
        settings = get_settings()
        since = datetime.now(timezone.utc) - timedelta(days=1)
        created_count = self.repository.count_created_since(db, since)
        max_runs = int(getattr(settings, "tenant_daily_run_quota", 200))
        if created_count >= max_runs:
            raise ConflictError("Daily run quota exceeded for tenant.")

    def _persist_analytics_artifact(self, db: Session, run, analytics: dict) -> None:
        settings = get_settings()
        tenant_id = db.info.get("tenant_id") or "unknown-tenant"
        artifact_uri = (
            f"file://./artifacts/{settings.artifact_prefix}/{tenant_id}/runs/{run.id}/analytics.json"
        )
        run.result_artifact_uri = self.artifact_storage.write_json(artifact_uri, analytics)