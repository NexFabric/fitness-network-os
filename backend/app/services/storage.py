"""Storage provider abstraction for secure report and media artifact storage.

Supports Local Storage fallback and S3/MinIO presigned URL generation.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

from app.core.config import settings


def _safe_component(value: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value:
        raise ValueError("invalid_artifact_name")
    return value


class StorageProvider(ABC):
    @abstractmethod
    async def save_bytes(
        self, tenant_id: UUID, artifact_id: str, data: bytes, filename: str
    ) -> str:
        """Save raw bytes to storage, return storage reference URI."""

    @abstractmethod
    async def generate_download_url(
        self, tenant_id: UUID, storage_uri: str, expires_in: int
    ) -> str:
        """Generate a tenant-bound, short-lived download URL."""

    @abstractmethod
    async def delete(self, tenant_id: UUID, storage_uri: str) -> None:
        """Delete an artifact after validating its tenant namespace."""


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.REPORT_STORAGE_DIR).resolve()

    async def save_bytes(
        self, tenant_id: UUID, artifact_id: str, data: bytes, filename: str
    ) -> str:
        artifact_id = _safe_component(artifact_id)
        filename = _safe_component(filename)
        tenant_dir = self.base_dir / str(tenant_id)
        artifact_dir = tenant_dir / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        filepath = (artifact_dir / filename).resolve()
        if tenant_dir not in filepath.parents:
            raise ValueError("invalid_artifact_path")

        def _write() -> None:
            filepath.write_bytes(data)

        await asyncio.to_thread(_write)
        return filepath.as_uri()

    async def generate_download_url(
        self, tenant_id: UUID, storage_uri: str, expires_in: int
    ) -> str:
        expected_root = (self.base_dir / str(tenant_id)).resolve()
        path = Path(storage_uri.removeprefix("file://")).resolve()
        if expected_root not in path.parents:
            raise ValueError("artifact_tenant_mismatch")
        return path.as_uri()

    async def delete(self, tenant_id: UUID, storage_uri: str) -> None:
        expected_root = (self.base_dir / str(tenant_id)).resolve()
        path = Path(storage_uri.removeprefix("file://")).resolve()
        if expected_root not in path.parents:
            raise ValueError("artifact_tenant_mismatch")

        def _delete() -> None:
            path.unlink(missing_ok=True)
            try:
                path.parent.rmdir()
            except OSError:
                pass

        await asyncio.to_thread(_delete)


class S3StorageProvider(StorageProvider):
    def __init__(self, bucket_name: str, endpoint_url: str | None = None):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url or None

    def _client(self):
        import boto3

        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=settings.S3_REGION_NAME or None,
        )

    async def save_bytes(
        self, tenant_id: UUID, artifact_id: str, data: bytes, filename: str
    ) -> str:
        artifact_id = _safe_component(artifact_id)
        filename = _safe_component(filename)
        key = f"{tenant_id}/{artifact_id}/{filename}"
        put_args: dict[str, object] = {
            "Bucket": self.bucket_name,
            "Key": key,
            "Body": data,
            "ContentType": "text/csv; charset=utf-8",
            "ServerSideEncryption": settings.S3_SSE_ALGORITHM,
        }
        if settings.S3_SSE_ALGORITHM == "aws:kms":
            put_args["SSEKMSKeyId"] = settings.S3_KMS_KEY_ID
        await asyncio.to_thread(self._client().put_object, **put_args)
        return f"s3://{self.bucket_name}/{key}"

    async def generate_download_url(
        self, tenant_id: UUID, storage_uri: str, expires_in: int
    ) -> str:
        prefix = f"s3://{self.bucket_name}/"
        if not storage_uri.startswith(prefix):
            raise ValueError("invalid_storage_uri")
        key = storage_uri.removeprefix(prefix)
        if not key.startswith(f"{tenant_id}/"):
            raise ValueError("artifact_tenant_mismatch")
        return await asyncio.to_thread(
            self._client().generate_presigned_url,
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )

    async def delete(self, tenant_id: UUID, storage_uri: str) -> None:
        prefix = f"s3://{self.bucket_name}/"
        if not storage_uri.startswith(prefix):
            raise ValueError("invalid_storage_uri")
        key = storage_uri.removeprefix(prefix)
        if not key.startswith(f"{tenant_id}/"):
            raise ValueError("artifact_tenant_mismatch")
        await asyncio.to_thread(
            self._client().delete_object,
            Bucket=self.bucket_name,
            Key=key,
        )


def get_storage_provider() -> StorageProvider:
    if settings.REPORT_STORAGE_PROVIDER.strip().lower() == "s3":
        if not settings.S3_BUCKET_NAME:
            raise RuntimeError("S3_BUCKET_NAME is required for S3 report storage")
        return S3StorageProvider(
            settings.S3_BUCKET_NAME,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
        )
    if settings.is_production:
        raise RuntimeError("Local report storage is forbidden in production")
    return LocalStorageProvider(settings.REPORT_STORAGE_DIR)
