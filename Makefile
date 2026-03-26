.PHONY: setup lint test run-local seed-benchmarks eval-gate-check

setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

lint:
	ruff check .
	black --check .
	mypy llm_eval_platform/api llm_eval_platform/core llm_eval_platform/models

test:
	pytest

run-local:
	docker compose up --build

seed-benchmarks:
	python llm_eval_platform/scripts/seed_benchmark_packs.py --list

eval-gate-check:
	python llm_eval_platform/scripts/ci_eval_gate.py \
		--baseline llm_eval_platform/fixtures/eval_gates/baseline.json \
		--candidate llm_eval_platform/fixtures/eval_gates/candidate.json