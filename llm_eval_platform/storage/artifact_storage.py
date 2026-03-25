from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from llm_eval_platform.core.config import get_settings
from llm_eval_platform.storage.s3_client import S3Client


class ArtifactStorage:
    def __init__(self, s3_client: S3Client | None = None) -> None:
        self.settings = get_settings()
        self.s3_client = s3_client or S3Client()

    def write_json(self, artifact_uri: str, payload: dict) -> str:
        parsed = urlparse(artifact_uri)
        raw = json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8")
        if parsed.scheme in {"", "file"}:
            path = Path(parsed.path if parsed.scheme == "file" else artifact_uri)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            return f"file://{path.resolve()}"
        if parsed.scheme == "s3":
            self.s3_client.upload_bytes(parsed.netloc, parsed.path.lstrip("/"), raw)
            return artifact_uri
        raise ValueError(f"Unsupported artifact scheme: {parsed.scheme}")

    def read_json(self, artifact_uri: str) -> dict:
        parsed = urlparse(artifact_uri)
        if parsed.scheme in {"", "file"}:
            path = Path(parsed.path if parsed.scheme == "file" else artifact_uri)
            return json.loads(path.read_text(encoding="utf-8"))
        if parsed.scheme == "s3":
            raw = self.s3_client.download_bytes(parsed.netloc, parsed.path.lstrip("/"))
            return json.loads(raw.decode("utf-8"))
        raise ValueError(f"Unsupported artifact scheme: {parsed.scheme}")
