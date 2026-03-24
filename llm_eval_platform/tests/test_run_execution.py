from __future__ import annotations

from pathlib import Path

from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import llm_eval_platform.models  # noqa: F401
from llm_eval_platform.core.database import Base
from llm_eval_platform.models.dataset import Dataset, DatasetVersion
from llm_eval_platform.models.experiment import Experiment
from llm_eval_platform.models.model_config import ModelConfig
from llm_eval_platform.models.prompt import Prompt, PromptVersion
from llm_eval_platform.models.run import Run
from llm_eval_platform.services.evaluation_engine.engine import EvaluationEngine
from llm_eval_platform.services.run_orchestration.orchestrator import RunOrchestrator
from llm_eval_platform.storage.dataset_storage import DatasetStorage
from llm_eval_platform.workers.evaluation_worker import process_evaluation_task
from llm_eval_platform.tasks.evaluation_task import EvaluationTask


class InMemoryDatasetStorage(DatasetStorage):
    def __init__(self, examples: list[dict]):
        self.examples = examples

    def load_examples(self, object_uri: str) -> list[dict]:
        return list(self.examples)


class RecordingQueue:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def enqueue(self, func: str, payload: dict) -> None:
        self.payloads.append(payload)


class FlakyMockClient:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, **kwargs):
        from llm_eval_platform.services.model_gateway.base_client import ModelResponse

        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("provider timed out")
        return ModelResponse(output_text="hello", metadata={"latency_ms": 1.2, "cost_usd": 0.01})


def build_session_factory(tmp_path: Path):
    db_path = tmp_path / "run-execution.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def seed_run(db: Session) -> Run:
    dataset = Dataset(name="demo-dataset", task_type="qa")
    prompt = Prompt(name="demo-prompt")
    experiment = Experiment(name="demo-experiment")
    model = ModelConfig(
        name="demo-model",
        provider="mock",
        model_name="mock-model",
        parameters={
            "mock_strategy": "expected_output",
            "retry_policy": {
                "max_attempts": 2,
                "backoff_seconds": 0.0,
                "max_backoff_seconds": 0.0,
            },
        },
    )
    db.add_all([dataset, prompt, experiment, model])
    db.flush()

    dataset_version = DatasetVersion(
        dataset_id=dataset.id,
        version=1,
        object_uri="memory://dataset.jsonl",
        example_count=2,
    )
    prompt_version = PromptVersion(
        prompt_id=prompt.id,
        version=1,
        template="Question: {question}\nAnswer:",
    )
    db.add_all([dataset_version, prompt_version])
    db.flush()

    run = Run(
        experiment_id=experiment.id,
        dataset_version_id=dataset_version.id,
        prompt_version_id=prompt_version.id,
        model_config_id=model.id,
        parameters={"metrics": ["exact_match", "semantic_similarity", "latency"]},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def test_orchestrator_and_worker_persist_aggregate_metrics(tmp_path: Path, monkeypatch) -> None:
    session_factory = build_session_factory(tmp_path)
    with session_factory() as db:
        run = seed_run(db)
        queue = RecordingQueue()
        orchestrator = RunOrchestrator(queue=queue)
        orchestrator.task_builder.dataset_storage = InMemoryDatasetStorage(
            [
                {"input": {"question": "alpha"}, "expected_output": {"answer": "A"}},
                {"input": {"question": "beta"}, "expected_output": {"answer": "B"}},
            ]
        )

        monkeypatch.setattr(
            "llm_eval_platform.workers.evaluation_worker.SessionLocal",
            session_factory,
        )

        queued_run = orchestrator.enqueue_run(db, run.id)
        assert queued_run.total_examples == 2
        assert len(queue.payloads) == 2

    for payload in queue.payloads:
        result = process_evaluation_task(payload)
        assert result["example_index"] in {0, 1}

    with session_factory() as db:
        finished_run = db.get(Run, run.id)
        assert finished_run is not None
        assert finished_run.status == "completed"
        assert finished_run.processed_examples == 2
        assert finished_run.completed_examples == 2
        assert finished_run.failed_examples == 0
        assert {metric.metric_name for metric in finished_run.metrics} >= {
            "average_score",
            "latency_avg_ms",
            "metric.exact_match.avg",
            "metric.semantic_similarity.avg",
        }


def test_engine_supports_expanded_metric_plugins() -> None:
    task = EvaluationTask(
    run_id=UUID("00000000-0000-0000-0000-000000000001"),
    example_index=0,
    input_payload={"question": "hi"},
    expected_output={"answer": "hello"},
    prompt_template="Question: {question}",
    model_provider="mock",
    model_name="mock-model",
    model_parameters={
        "retry_policy": {
            "max_attempts": 2,
            "backoff_seconds": 0.0,
            "max_backoff_seconds": 0.0,
        }
    },
    metrics=["exact_match"],
    )
    engine = EvaluationEngine()
    result = engine.execute(task)
    assert result["metadata"]["attempt_count"] == 1
    assert set(result["metadata"]["metric_scores"]) == {
        "exact_match",
        "semantic_similarity",
        "llm_judge",
        "latency",
        "cost",
    }


def test_engine_retries_transient_provider_failures(monkeypatch) -> None:
    flaky_client = FlakyMockClient()
    monkeypatch.setattr(
        EvaluationEngine,
        "_resolve_client",
        staticmethod(lambda provider: flaky_client),
    )

    task = EvaluationTask(
    run_id=UUID("00000000-0000-0000-0000-000000000001"),
    example_index=0,
    input_payload={"question": "hi"},
    expected_output={"answer": "hello"},
    prompt_template="Question: {question}",
    model_provider="mock",
    model_name="mock-model",
    model_parameters={
        "retry_policy": {
            "max_attempts": 2,
            "backoff_seconds": 0.0,
            "max_backoff_seconds": 0.0,
        }
    },
    metrics=["exact_match"],
    )
    result = EvaluationEngine().execute(task)
    assert flaky_client.calls == 2
    assert result["metadata"]["attempt_count"] == 2
    assert result["metadata"]["retry_count"] == 1
    assert result["metadata"]["retry_history"][0]["category"] == "provider_timeout"
