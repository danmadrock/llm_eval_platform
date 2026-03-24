from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trigger a Phase 2 evaluation run through the API."
    )
    parser.add_argument("--base-url", default="http://localhost:8000/api/v1")
    parser.add_argument("--dataset-path", required=True)
    args = parser.parse_args()

    dataset_path = Path(args.dataset_path).resolve()
    records = [
        {"input": {"question": "Capital of France?"}, "expected_output": {"answer": "Paris"}},
        {"input": {"question": "2 + 2?"}, "expected_output": {"answer": "4"}},
    ]
    dataset_path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )

    dataset = requests.post(
        f"{args.base_url}/datasets",
        json={
            "name": "local-phase2-dataset",
            "description": "Local phase 2 demo",
            "task_type": "qa",
        },
        timeout=30,
    ).json()["data"]

    dataset_version = requests.post(
        f"{args.base_url}/datasets/{dataset['id']}/versions",
        json={"object_uri": str(dataset_path), "example_count": len(records)},
        timeout=30,
    ).json()["data"]

    prompt = requests.post(
        f"{args.base_url}/prompts",
        json={"name": "local-phase2-prompt", "description": "Prompt for local demo"},
        timeout=30,
    ).json()["data"]
    prompt_version = requests.post(
        f"{args.base_url}/prompts/{prompt['id']}/versions",
        json={"template": "Answer the question.\nQuestion: {question}\nAnswer:"},
        timeout=30,
    ).json()["data"]

    model = requests.post(
        f"{args.base_url}/models",
        json={
            "name": "local-mock-model",
            "provider": "mock",
            "model_name": "mock-answerer",
            "parameters": {"mock_strategy": "expected_output"},
            "description": "Local deterministic model",
        },
        timeout=30,
    ).json()["data"]

    experiment = requests.post(
        f"{args.base_url}/experiments",
        json={"name": "local-phase2-experiment", "description": "Phase 2 local run"},
        timeout=30,
    ).json()["data"]

    run = requests.post(
        f"{args.base_url}/runs",
        json={
            "experiment_id": experiment["id"],
            "dataset_version_id": dataset_version["id"],
            "prompt_version_id": prompt_version["id"],
            "model_config_id": model["id"],
            "parameters": {"metrics": ["exact_match"]},
        },
        timeout=30,
    ).json()["data"]

    started = requests.post(
        f"{args.base_url}/runs/{run['id']}/start",
        timeout=30,
    ).json()["data"]
    print(json.dumps({"run": started}, indent=2))


if __name__ == "__main__":
    main()