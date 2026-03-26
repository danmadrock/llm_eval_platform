from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate candidate run metrics against baseline thresholds.")
    parser.add_argument("--baseline", required=True, help="Path to baseline analytics JSON")
    parser.add_argument("--candidate", required=True, help="Path to candidate analytics JSON")
    parser.add_argument("--max-score-drop", type=float, default=0.02)
    parser.add_argument("--max-cost-increase", type=float, default=0.10)
    parser.add_argument("--max-failure-rate-increase", type=float, default=0.05)
    args = parser.parse_args()

    baseline = _load(args.baseline)
    candidate = _load(args.candidate)

    baseline_kpis = baseline.get("kpis", {})
    candidate_kpis = candidate.get("kpis", {})
    baseline_examples = baseline.get("examples", {})
    candidate_examples = candidate.get("examples", {})

    baseline_score = float(baseline_kpis.get("average_score") or 0.0)
    candidate_score = float(candidate_kpis.get("average_score") or 0.0)

    baseline_cost = float(baseline_kpis.get("total_cost_usd") or 0.0)
    candidate_cost = float(candidate_kpis.get("total_cost_usd") or 0.0)

    def failure_rate(examples: dict) -> float:
        total = int(examples.get("total") or 0)
        failed = int(examples.get("failed") or 0)
        if total <= 0:
            return 0.0
        return failed / total

    base_failure = failure_rate(baseline_examples)
    cand_failure = failure_rate(candidate_examples)

    score_drop = baseline_score - candidate_score
    cost_increase = 0.0 if baseline_cost <= 0 else (candidate_cost - baseline_cost) / baseline_cost
    failure_increase = cand_failure - base_failure

    failures: list[str] = []
    if score_drop > args.max_score_drop:
        failures.append(
            f"score_drop={score_drop:.4f} exceeds max_score_drop={args.max_score_drop:.4f}"
        )
    if cost_increase > args.max_cost_increase:
        failures.append(
            f"cost_increase={cost_increase:.4f} exceeds max_cost_increase={args.max_cost_increase:.4f}"
        )
    if failure_increase > args.max_failure_rate_increase:
        failures.append(
            "failure_rate_increase="
            f"{failure_increase:.4f} exceeds max_failure_rate_increase={args.max_failure_rate_increase:.4f}"
        )

    print(
        json.dumps(
            {
                "baseline_score": baseline_score,
                "candidate_score": candidate_score,
                "score_drop": score_drop,
                "baseline_cost": baseline_cost,
                "candidate_cost": candidate_cost,
                "cost_increase": cost_increase,
                "baseline_failure_rate": base_failure,
                "candidate_failure_rate": cand_failure,
                "failure_rate_increase": failure_increase,
                "gate_passed": not failures,
                "violations": failures,
            },
            indent=2,
        )
    )

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
