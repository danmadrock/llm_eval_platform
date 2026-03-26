from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import llm_eval_platform.models  # noqa: F401
from llm_eval_platform.api.main import app
from llm_eval_platform.core.database import Base, get_db
from llm_eval_platform.models.dataset import Dataset, DatasetVersion
from llm_eval_platform.models.evaluation_result import EvaluationResult
from llm_eval_platform.models.experiment import Experiment
from llm_eval_platform.models.model_config import ModelConfig
from llm_eval_platform.models.prompt import Prompt, PromptVersion
from llm_eval_platform.models.run import Run


def _client(tmp_path: Path) -> tuple[TestClient, sessionmaker]:
    db_path = tmp_path / "phase5.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = session_local()
        try:
            db.info["tenant_id"] = "tenant-dev"
            db.info["principal_id"] = "dev-admin"
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    client.headers.update({"X-API-Key": "dev-admin"})
    return client, session_local


def _seed_run(session_local: sessionmaker) -> tuple[str, str, str]:
    with session_local() as db:
        tenant_id = "tenant-dev"
        dataset = Dataset(name="phase5-ds", task_type="qa", tenant_id=tenant_id)
        db.add(dataset)
        db.flush()
        dataset_version = DatasetVersion(
            dataset_id=dataset.id,
            version=1,
            object_uri="s3://datasets/phase5/v1.jsonl",
            example_count=10,
            tenant_id=tenant_id,
        )
        db.add(dataset_version)

        prompt = Prompt(name="phase5-prompt", tenant_id=tenant_id)
        db.add(prompt)
        db.flush()
        prompt_version = PromptVersion(prompt_id=prompt.id, version=1, template="Q: {question}\nA:", tenant_id=tenant_id)
        db.add(prompt_version)

        model = ModelConfig(name="phase5-model", model_name="gpt-4o-mini", parameters={}, tenant_id=tenant_id)
        db.add(model)

        experiment = Experiment(name="phase5-exp", tenant_id=tenant_id)
        db.add(experiment)
        db.flush()

        run = Run(
            experiment_id=experiment.id,
            dataset_version_id=dataset_version.id,
            prompt_version_id=prompt_version.id,
            model_config_id=model.id,
            tenant_id=tenant_id,
            total_examples=10,
            processed_examples=10,
            completed_examples=8,
            failed_examples=2,
        )
        db.add(run)
        db.flush()

        result = EvaluationResult(
            run_id=run.id,
            example_index=0,
            input_payload={"question": "What is policy?"},
            actual_output={"answer": "Policy is ..."},
            score=0.8,
            status="failed",
            result_metadata={"latency_ms": 2100, "cost_usd": 0.2},
            tenant_id=tenant_id,
        )
        db.add(result)

        db.commit()
        return str(experiment.id), str(run.id), str(result.id)


def test_phase5_frontier_optimization_and_human_review(tmp_path: Path) -> None:
    client, session_local = _client(tmp_path)
    experiment_id, run_id, result_id = _seed_run(session_local)

    assert client.get(f"/api/v1/runs/{run_id}/analytics").status_code == 200

    frontier = client.get(f"/api/v1/comparisons/experiments/{experiment_id}/quality-cost-frontier")
    assert frontier.status_code == 200
    assert frontier.json()["data"]["total_runs"] == 1

    hook = client.post(f"/api/v1/optimization/runs/{run_id}/hook")
    assert hook.status_code == 200
    assert hook.json()["data"]["hook_type"] == "prompt_optimization_signal"

    queue = client.get(f"/api/v1/human-review/runs/{run_id}/queue")
    assert queue.status_code == 200
    assert queue.json()["pagination"]["total"] == 1

    claim = client.post(f"/api/v1/human-review/results/{result_id}/claim", json={"reviewer": "alice"})
    assert claim.status_code == 200
    assert claim.json()["data"]["human_review"]["status"] == "in_review"

    submit = client.post(
        f"/api/v1/human-review/results/{result_id}/submit",
        json={"reviewer": "alice", "decision": "approved", "notes": "Looks good", "score_override": 0.95},
    )
    assert submit.status_code == 200
    assert submit.json()["data"]["score"] == 0.95
