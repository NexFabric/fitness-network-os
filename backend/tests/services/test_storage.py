from uuid import uuid4

import pytest

from app.services.storage import S3StorageProvider


class FakeS3Client:
    def __init__(self) -> None:
        self.put: dict[str, object] | None = None
        self.presign: dict[str, object] | None = None
        self.deleted: dict[str, object] | None = None

    def put_object(self, **kwargs: object) -> None:
        self.put = kwargs

    def generate_presigned_url(
        self, operation: str, *, Params: dict[str, str], ExpiresIn: int
    ) -> str:
        self.presign = {
            "operation": operation,
            "Params": Params,
            "ExpiresIn": ExpiresIn,
        }
        return "https://objects.example.test/signed"

    def delete_object(self, **kwargs: object) -> None:
        self.deleted = kwargs


@pytest.mark.asyncio
async def test_s3_storage_uploads_encrypted_and_presigns_tenant_key(monkeypatch):
    tenant_id = uuid4()
    fake = FakeS3Client()
    provider = S3StorageProvider("private-reports")
    monkeypatch.setattr(provider, "_client", lambda: fake)

    uri = await provider.save_bytes(tenant_id, "run-1", b"a,b\n1,2\n", "report.csv")
    assert uri == f"s3://private-reports/{tenant_id}/run-1/report.csv"
    assert fake.put is not None
    assert fake.put["ServerSideEncryption"] == "AES256"
    assert fake.put["ContentType"] == "text/csv; charset=utf-8"

    url = await provider.generate_download_url(tenant_id, uri, 900)
    assert url == "https://objects.example.test/signed"
    assert fake.presign == {
        "operation": "get_object",
        "Params": {
            "Bucket": "private-reports",
            "Key": f"{tenant_id}/run-1/report.csv",
        },
        "ExpiresIn": 900,
    }

    await provider.delete(tenant_id, uri)
    assert fake.deleted == {
        "Bucket": "private-reports",
        "Key": f"{tenant_id}/run-1/report.csv",
    }


@pytest.mark.asyncio
async def test_s3_storage_refuses_cross_tenant_presign(monkeypatch):
    provider = S3StorageProvider("private-reports")
    monkeypatch.setattr(provider, "_client", lambda: FakeS3Client())
    other_tenant = uuid4()
    with pytest.raises(ValueError, match="artifact_tenant_mismatch"):
        await provider.generate_download_url(
            uuid4(),
            f"s3://private-reports/{other_tenant}/run-1/report.csv",
            900,
        )
