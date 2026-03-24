from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class DatasetStorage:
    """Reads dataset examples from local JSONL artifacts for the Phase 2 slice."""

    def load_examples(self, object_uri: str) -> list[dict[str, Any]]:
        path = self._resolve_local_path(object_uri)
        examples: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError(f"Dataset record on line {line_number} must be a JSON object.")
                examples.append(record)
        return examples

    @staticmethod
    def _resolve_local_path(object_uri: str) -> Path:
        parsed = urlparse(object_uri)
        if parsed.scheme in {"", "file"}:
            candidate = parsed.path if parsed.scheme == "file" else object_uri
            path = Path(candidate)
            if not path.is_absolute():
                path = Path.cwd() / path
            return path.resolve()
        raise ValueError("Phase 2 dataset loading only supports local paths or file:// URIs.")