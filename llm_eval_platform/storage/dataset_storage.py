from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from llm_eval_platform.storage.s3_client import S3Client

class DatasetStorage:
    """Reads dataset examples from local or S3-backed JSONL artifacts."""

    def __init__(self, s3_client: S3Client | None = None) -> None:
        self.s3_client = s3_client or S3Client()


    def load_examples(self, object_uri: str) -> list[dict[str, Any]]:
        parsed = urlparse(object_uri)
        if parsed.scheme == "s3":
            raw = self.s3_client.download_bytes(parsed.netloc, parsed.path.lstrip("/"))
            return self._load_jsonl_lines(raw.decode("utf-8").splitlines())
        path = self._resolve_local_path(object_uri)
        return self._load_jsonl_lines(path.read_text(encoding="utf-8").splitlines())

    def _load_jsonl_lines(self, lines: list[str]) -> list[dict[str, Any]]:
        examples: list[dict[str, Any]] = []
        for line_number, raw_line in enumerate(lines, start=1):
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
        raise ValueError("Dataset loading supports local paths, file:// URIs, and s3:// URIs.")