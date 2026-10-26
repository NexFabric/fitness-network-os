# S3 Report Storage — Runtime Proof (P1-3b-RT)

**Date:** 2026-08-16 · **Status:** **EXECUTED against a real S3 API (MinIO)**

Until now the S3 report-storage path was covered only by unit tests with a
mocked client. This drill runs the **actual `S3StorageProvider`** against a real
S3 API server, so the encrypted write, the presigned read and the tenant-scoped
delete are proven against a server that can reject them.

## Run it

```bash
docker compose -f docker-compose.yml -f docker-compose.storage.yml up -d minio minio-init
cd backend && ./.venv/bin/python scripts/s3_runtime_proof.py
```

- Server: `docker-compose.storage.yml` (MinIO, private bucket, KMS key set so
  server-side encryption is actually enforceable)
- Drill: `backend/scripts/s3_runtime_proof.py`

## Result — 10/10 PASS

```
PASS  provider-selection    S3StorageProvider bucket=fitness-os-reports
PASS  put-object            s3://fitness-os-reports/<tenant>/<artifact>/report.csv
PASS  head-object           bytes=60
PASS  sse-at-rest           ServerSideEncryption=AES256
PASS  tenant-key-layout     key prefix == tenant_id
PASS  bucket-private        anonymous GET rejected with 403
PASS  presign               expires_in=60
PASS  presigned-get         status=200 bytes=60 match=True
PASS  cross-tenant-presign  ValueError artifact_tenant_mismatch
PASS  delete                object gone after delete
```

## What this proved that mocks could not

1. **Encryption is really enforced.** The first run *failed*: MinIO rejected the
   write with `NotImplemented — KMS not configured`. That is direct evidence the
   application genuinely sends `ServerSideEncryption` on every PutObject rather
   than merely claiming to. The object store had to be given a key before the
   write could succeed.
2. **The bucket is not publicly readable** — an anonymous GET of the exact key
   returns 403.
3. **The presigned URL actually serves the bytes** over HTTP, and the returned
   payload is byte-identical to what was written.
4. **Cross-tenant access is refused by the provider itself**, before any URL is
   minted (`artifact_tenant_mismatch`), so a tenant-id mix-up cannot leak a
   signed link.

## What this does NOT close

MinIO is S3-compatible, not AWS. Still open and **not** claimed by this document:

- A real **AWS S3 bucket** in staging/production with its own bucket policy,
  public-access block and lifecycle rules.
- **SSE-KMS** with a production CMK (`S3_SSE_ALGORITHM=aws:kms` +
  `S3_KMS_KEY_ID`); this drill exercised `AES256`.
- The **IAM policy and credential rotation** for the application principal —
  tracked separately as P2-3-IAM (`docs/ops/KMS_IAM_RUNBOOK.md`).

P1-3b-RT is closed for *code correctness against a real S3 API*. The production
bucket/IAM evidence remains an infrastructure task.
