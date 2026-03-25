from __future__ import annotations

import io

import boto3


class S3Client:
    def __init__(self, endpoint_url: str | None = None) -> None:
        self._client = boto3.client("s3", endpoint_url=endpoint_url)

    def upload_bytes(self, bucket: str, key: str, payload: bytes, content_type: str = "application/json") -> None:
        self._client.put_object(Bucket=bucket, Key=key, Body=io.BytesIO(payload), ContentType=content_type)

    def download_bytes(self, bucket: str, key: str) -> bytes:
        response = self._client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()