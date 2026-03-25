from __future__ import annotations

from llm_eval_platform.core.config import get_settings


class RegressionService:
    def evaluate(self, baseline_analytics: dict, candidate_analytics: dict) -> dict:
        settings = get_settings()
        baseline_score = baseline_analytics["kpis"].get("average_score")
        candidate_score = candidate_analytics["kpis"].get("average_score")
        baseline_fail = self._failure_rate(baseline_analytics)
        candidate_fail = self._failure_rate(candidate_analytics)

        reasons: list[str] = []
        score_delta = None
        failure_rate_delta = None

        if baseline_score is not None and candidate_score is not None:
            score_delta = candidate_score - baseline_score
            if score_delta < -settings.regression_score_drop_threshold:
                reasons.append("average_score_dropped")

        if baseline_fail is not None and candidate_fail is not None:
            failure_rate_delta = candidate_fail - baseline_fail
            if failure_rate_delta > settings.regression_failure_rate_increase_threshold:
                reasons.append("failure_rate_increased")

        status = "pass" if not reasons else "regression"
        return {
            "status": status,
            "score_delta": score_delta,
            "failure_rate_delta": failure_rate_delta,
            "policy_thresholds": {
                "score_drop": settings.regression_score_drop_threshold,
                "failure_rate_increase": settings.regression_failure_rate_increase_threshold,
            },
            "reasons": reasons,
        }

    @staticmethod
    def _failure_rate(analytics: dict) -> float | None:
        examples = analytics.get("examples", {})
        total = examples.get("total")
        failed = examples.get("failed")
        if not total:
            return None
        return float(failed) / float(total)
