#!/usr/bin/env python
"""P1-3b-RT runtime proof: exercise the real S3StorageProvider against a real
S3 API server (MinIO), not a mock.

    docker compose -f docker-compose.yml -f docker-compose.storage.yml up -d minio minio-init
    cd backend && ./.venv/bin/python scripts/s3_runtime_proof.py

Checks, in order:
  1. put_object writes the object with server-side encryption
  2. the object is really in the bucket, with the tenant-scoped key layout
  3. the bucket rejects anonymous reads (private)
  4. generate_download_url returns a presigned URL that actually serves the bytes
  5. a presigned URL for another tenant's prefix is refused by the provider
  6. delete removes the object

Exits non-zero on the first failure. Prints a machine-readable summary so the
result can be pasted into docs/ops/S3_RUNTIME_PROOF.md without embellishment.
"""

from __future__ import annotations

import os
import sys
import urllib.request
from urllib.error import HTTPError
from uuid import uuid4

# Configure the app settings BEFORE importing them.
os.environ.setdefault("REPORT_STORAGE_PROVIDER", "s3")
os.environ.setdefault("S3_BUCKET_NAME", "fitness-os-reports")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_REGION_NAME", "us-east-1")
os.environ.setdefault("S3_SSE_ALGORITHM", "AES256")
os.environ.setdefault(
    "AWS_ACCESS_KEY_ID", os.environ.get("MINIO_ROOT_USER", "fitnessminio")
)
os.environ.setdefault(
    "AWS_SECRET_ACCESS_KEY", os.environ.get("MINIO_ROOT_PASSWORD", "fitnessminio123")
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from app.services.storage import S3StorageProvider, get_storage_provider

PASSED: list[str] = []


def ok(step: str, detail: str = "") -> None:
    PASSED.append(step)
    print(f"PASS  {step}" + (f" — {detail}" if detail else ""))


def die(step: str, detail: str) -> None:
    print(f"FAIL  {step} — {detail}")
    sys.exit(1)


async def _http_get(url: str) -> tuple[int, bytes]:
    """Blocking urllib off the event loop, the same way storage.py handles boto3."""

    def _fetch() -> tuple[int, bytes]:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return resp.status, resp.read()

    return await asyncio.to_thread(_fetch)


async def main() -> None:
    provider = get_storage_provider()
    if not isinstance(provider, S3StorageProvider):
        die(
            "provider-selection",
            f"expected S3StorageProvider, got {type(provider).__name__}",
        )
    ok("provider-selection", f"{type(provider).__name__} bucket={provider.bucket_name}")

    tenant_id = uuid4()
    other_tenant_id = uuid4()
    artifact_id = uuid4()
    payload = f"member,visits\nproof-{artifact_id},42\n".encode()

    # 1. write
    try:
        uri = await provider.save_bytes(tenant_id, artifact_id, payload)
    except Exception as exc:
        die("put-object", f"{type(exc).__name__}: {exc}")
    ok("put-object", uri)

    client = provider._client()
    key = uri.removeprefix(f"s3://{provider.bucket_name}/")

    # 2. object really exists, with SSE applied
    try:
        head = client.head_object(Bucket=provider.bucket_name, Key=key)
    except Exception as exc:
        die("head-object", f"{type(exc).__name__}: {exc}")
    if head["ContentLength"] != len(payload):
        die("head-object", f"size mismatch {head['ContentLength']} != {len(payload)}")
    sse = head.get("ServerSideEncryption")
    if sse != "AES256":
        die("sse-at-rest", f"expected AES256, got {sse!r}")
    ok("head-object", f"key={key} bytes={head['ContentLength']}")
    ok("sse-at-rest", f"ServerSideEncryption={sse}")

    if not key.startswith(f"{tenant_id}/"):
        die("tenant-key-layout", f"key not tenant-scoped: {key}")
    ok("tenant-key-layout", f"{key.split('/')[0]} == tenant_id")

    # 3. bucket must not be publicly readable
    public_url = f"{os.environ['S3_ENDPOINT_URL']}/{provider.bucket_name}/{key}"
    try:
        await _http_get(public_url)
    except HTTPError as exc:
        if exc.code not in (401, 403):
            die("bucket-private", f"unexpected status {exc.code}")
        ok("bucket-private", f"anonymous GET rejected with {exc.code}")
    except Exception as exc:
        die("bucket-private", f"{type(exc).__name__}: {exc}")
    else:
        die("bucket-private", "anonymous GET succeeded — bucket is public")

    # 4. presigned URL actually serves the bytes
    try:
        url = await provider.generate_download_url(tenant_id, uri, expires_in=60)
    except Exception as exc:
        die("presign", f"{type(exc).__name__}: {exc}")
    try:
        status, body = await _http_get(url)
    except Exception as exc:
        die("presigned-get", f"{type(exc).__name__}: {exc}")
    if status != 200 or body != payload:
        die("presigned-get", f"status={status} bytes_match={body == payload}")
    ok("presign", f"expires_in=60 len={len(url)}")
    ok("presigned-get", f"status=200 bytes={len(body)} match=True")

    # 5. cross-tenant presign must be refused by the provider itself
    try:
        await provider.generate_download_url(other_tenant_id, uri, expires_in=60)
    except ValueError as exc:
        if str(exc) != "artifact_tenant_mismatch":
            die("cross-tenant-presign", f"wrong error: {exc}")
        ok("cross-tenant-presign", "ValueError artifact_tenant_mismatch")
    except Exception as exc:
        die("cross-tenant-presign", f"{type(exc).__name__}: {exc}")
    else:
        die("cross-tenant-presign", "provider issued a URL for another tenant")

    # 6. delete
    try:
        await provider.delete(tenant_id, uri)
    except Exception as exc:
        die("delete", f"{type(exc).__name__}: {exc}")
    try:
        client.head_object(Bucket=provider.bucket_name, Key=key)
    except Exception:
        ok("delete", "object gone after delete")
    else:
        die("delete", "object still present after delete")

    print(
        f"\nALL PASS — {len(PASSED)} checks against a real S3 API at "
        f"{os.environ['S3_ENDPOINT_URL']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
