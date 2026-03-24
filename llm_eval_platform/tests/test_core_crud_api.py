from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import llm_eval_platform.models  # noqa: F401
from llm_eval_platform.api.main import app
from llm_eval_platform.core.database import Base, get_db


@pytest.fixture()
def client(tmp_path: Path):
    db_path = tmp_path / "crud.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_core_crud_workflow(client: TestClient) -> None:
    dataset = client.post(
        "/api/v1/datasets",
        json={"name": "support-qa", "description": "Support benchmark", "task_type": "qa"},
    )
    assert dataset.status_code == 201
    dataset_id = dataset.json()["data"]["id"]

    dataset_version = client.post(
        f"/api/v1/datasets/{dataset_id}/versions",
        json={"object_uri": "s3://datasets/support-qa/v1.jsonl", "example_count": 120},
    )
    assert dataset_version.status_code == 201
    dataset_version_id = dataset_version.json()["data"]["id"]
    assert dataset_version.json()["data"]["version"] == 1

    prompt = client.post(
        "/api/v1/prompts",
        json={"name": "support-prompt", "description": "Prompt for support evals"},
    )
    assert prompt.status_code == 201
    prompt_id = prompt.json()["data"]["id"]

    prompt_version = client.post(
        f"/api/v1/prompts/{prompt_id}/versions",
        json={"template": "You are a helpful assistant.\nQuestion: {question}\nAnswer:"},
    )
    assert prompt_version.status_code == 201
    prompt_version_id = prompt_version.json()["data"]["id"]
    assert prompt_version.json()["data"]["version"] == 1

    model_config = client.post(
        "/api/v1/models",
        json={
            "name": "gpt4o-baseline",
            "provider": "openai",
            "model_name": "gpt-4o",
            "parameters": {"temperature": 0, "max_tokens": 256},
            "description": "Baseline config",
        },
    )
    assert model_config.status_code == 201
    model_config_id = model_config.json()["data"]["id"]

    experiment = client.post(
        "/api/v1/experiments",
        json={"name": "support-eval", "description": "Baseline comparison experiment"},
    )
    assert experiment.status_code == 201
    experiment_id = experiment.json()["data"]["id"]

    run = client.post(
        "/api/v1/runs",
        json={
            "experiment_id": experiment_id,
            "dataset_version_id": dataset_version_id,
            "prompt_version_id": prompt_version_id,
            "model_config_id": model_config_id,
            "parameters": {"batch_size": 10},
        },
    )
    assert run.status_code == 201
    run_id = run.json()["data"]["id"]

    updated_run = client.patch(
        f"/api/v1/runs/{run_id}",
        json={"status": "running", "started_at": "2026-03-19T10:00:00Z"},
    )
    assert updated_run.status_code == 200
    assert updated_run.json()["data"]["status"] == "running"
    assert updated_run.json()["data"]["processed_examples"] == 0

    result = client.post(
        "/api/v1/results",
        json={
            "run_id": run_id,
            "example_index": 0,
            "input_payload": {"question": "Reset password?"},
            "expected_output": {"answer": "Use reset link"},
            "actual_output": {"answer": "Click reset password"},
            "score": 0.92,
            "status": "completed",
            "metadata": {"latency_ms": 123},
        },
    )
    assert result.status_code == 201
    result_id = result.json()["data"]["id"]

    fetched_dataset = client.get(f"/api/v1/datasets/{dataset_id}")
    assert fetched_dataset.status_code == 200
    assert fetched_dataset.json()["data"]["versions"][0]["id"] == dataset_version_id

    prompt_versions = client.get(f"/api/v1/prompts/{prompt_id}/versions")
    assert prompt_versions.status_code == 200
    assert len(prompt_versions.json()["data"]) == 1

    results = client.get(f"/api/v1/results?run_id={run_id}")
    assert results.status_code == 200
    assert results.json()["pagination"]["total"] == 1
    assert results.json()["data"][0]["id"] == result_id

    update_result = client.patch(
        f"/api/v1/results/{result_id}",
        json={"score": 1.0, "metadata": {"latency_ms": 100}},
    )
    assert update_result.status_code == 200
    assert update_result.json()["data"]["score"] == 1.0

    list_datasets = client.get("/api/v1/datasets?limit=10&offset=0")
    assert list_datasets.status_code == 200
    assert list_datasets.json()["pagination"] == {"limit": 10, "offset": 0, "total": 1}

    delete_result = client.delete(f"/api/v1/results/{result_id}")
    assert delete_result.status_code == 204

    delete_run = client.delete(f"/api/v1/runs/{run_id}")
    assert delete_run.status_code == 204


def test_error_responses(client: TestClient) -> None:
    missing_dataset = client.get("/api/v1/datasets/00000000-0000-0000-0000-000000000000")
    assert missing_dataset.status_code == 404
    assert missing_dataset.json()["error"]["code"] == "resource_not_found"

    invalid_payload = client.post("/api/v1/datasets", json={"name": "", "task_type": "qa"})
    assert invalid_payload.status_code == 422
    assert invalid_payload.json()["error"]["code"] == "validation_error"

    duplicate_dataset = client.post(
        "/api/v1/datasets",
        json={"name": "dupe", "description": None, "task_type": "qa"},
    )
    assert duplicate_dataset.status_code == 201

    duplicate_dataset_again = client.post(
        "/api/v1/datasets",
        json={"name": "dupe", "description": None, "task_type": "qa"},
    )
    assert duplicate_dataset_again.status_code == 409
    assert duplicate_dataset_again.json()["error"]["code"] == "resource_conflict"