from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_ci_eval_gate_passes_with_default_fixture() -> None:
    cmd = [
        "python",
        "llm_eval_platform/scripts/ci_eval_gate.py",
        "--baseline",
        "llm_eval_platform/fixtures/eval_gates/baseline.json",
        "--candidate",
        "llm_eval_platform/fixtures/eval_gates/candidate.json",
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["gate_passed"] is True


def test_ci_eval_gate_fails_on_strict_threshold(tmp_path: Path) -> None:
    baseline = tmp_path / "base.json"
    candidate = tmp_path / "cand.json"
    baseline.write_text(json.dumps({"kpis": {"average_score": 0.9, "total_cost_usd": 1.0}, "examples": {"total": 10, "failed": 0}}))
    candidate.write_text(json.dumps({"kpis": {"average_score": 0.7, "total_cost_usd": 1.5}, "examples": {"total": 10, "failed": 3}}))

    cmd = [
        "python",
        "llm_eval_platform/scripts/ci_eval_gate.py",
        "--baseline",
        str(baseline),
        "--candidate",
        str(candidate),
        "--max-score-drop",
        "0.01",
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["gate_passed"] is False
    assert payload["violations"]