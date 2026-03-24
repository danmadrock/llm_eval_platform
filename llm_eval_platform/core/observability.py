from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import inf
from threading import Lock
from typing import Any


@dataclass(slots=True)
class HistogramSnapshot:
    count: int
    total: float
    bucket_counts: dict[float, int]


class PrometheusLikeMetrics:
    """Tiny in-process metrics collector with Prometheus text exposition format."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(dict)
        self._histograms: dict[str, dict[str, Any]] = {}

    def inc(self, metric: str, *, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        with self._lock:
            key = self._label_key(labels)
            current = self._counters[metric].get(key, 0.0)
            self._counters[metric][key] = current + value

    def observe(
        self,
        metric: str,
        value: float,
        *,
        labels: dict[str, str] | None = None,
        buckets: tuple[float, ...] = (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
    ) -> None:
        with self._lock:
            definition = self._histograms.setdefault(
                metric,
                {
                    "buckets": tuple(sorted(buckets)),
                    "samples": defaultdict(
                        lambda: {"count": 0, "sum": 0.0, "bucket_counts": defaultdict(int)}
                    ),
                },
            )
            label_key = self._label_key(labels)
            sample = definition["samples"][label_key]
            sample["count"] += 1
            sample["sum"] += value
            for bucket in definition["buckets"]:
                if value <= bucket:
                    sample["bucket_counts"][bucket] += 1
            sample["bucket_counts"][inf] += 1

    def get_counter_value(self, metric: str, *, labels: dict[str, str] | None = None) -> float:
        key = self._label_key(labels)
        return float(self._counters.get(metric, {}).get(key, 0.0))

    def get_histogram_snapshot(
        self, metric: str, *, labels: dict[str, str] | None = None
    ) -> HistogramSnapshot:
        definition = self._histograms.get(metric)
        if definition is None:
            return HistogramSnapshot(count=0, total=0.0, bucket_counts={})
        key = self._label_key(labels)
        sample = definition["samples"].get(key)
        if sample is None:
            return HistogramSnapshot(count=0, total=0.0, bucket_counts={})
        return HistogramSnapshot(
            count=int(sample["count"]),
            total=float(sample["sum"]),
            bucket_counts={
                float(bucket): int(count) for bucket, count in sample["bucket_counts"].items()
            },
        )

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            for metric, values in sorted(self._counters.items()):
                lines.append(f"# TYPE {metric} counter")
                for label_key, value in sorted(values.items()):
                    lines.append(f"{metric}{self._format_labels(label_key)} {value}")
            for metric, definition in sorted(self._histograms.items()):
                lines.append(f"# TYPE {metric} histogram")
                for label_key, sample in sorted(definition["samples"].items()):
                    for bucket in definition["buckets"]:
                        count = sample["bucket_counts"].get(bucket, 0)
                        bucket_labels = tuple(sorted((*label_key, ("le", str(bucket)))))
                        lines.append(f"{metric}_bucket{self._format_labels(bucket_labels)} {count}")
                    inf_labels = tuple(sorted((*label_key, ("le", "+Inf"))))
                    lines.append(
                        f"{metric}_bucket{self._format_labels(inf_labels)} "
                        f"{sample['bucket_counts'].get(inf, 0)}"
                    )
                    lines.append(
                        f"{metric}_count{self._format_labels(label_key)} {sample['count']}"
                    )
                    lines.append(f"{metric}_sum{self._format_labels(label_key)} {sample['sum']}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _label_key(labels: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
        if not labels:
            return tuple()
        return tuple(sorted((str(k), str(v)) for k, v in labels.items()))

    @staticmethod
    def _format_labels(label_key: tuple[tuple[str, str], ...]) -> str:
        if not label_key:
            return ""
        rendered = ",".join(f'{name}="{value}"' for name, value in label_key)
        return "{" + rendered + "}"


metrics = PrometheusLikeMetrics()
