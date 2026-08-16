# KMS / IAM Runbook — P2-3-IAM

**Date:** 2026-08-16 · **Status:** **ARTIFACTS LANDED · NOT VERIFIED**

Read that status literally. The policies, the runbook and the verification
script are in the repo. **Nothing has been executed against a real AWS
account**, because this machine has no AWS credentials. P2-3-IAM stays open
until `backend/scripts/kms_iam_verify.py` prints `ALL PASS` against a real CMK.

## What the code actually needs

| Where | Operation | Env |
|---|---|---|
| `app/core/qr_crypto.py` | `kms:GenerateDataKey` (AES_256), `kms:Decrypt` | `QR_KMS_MODE=aws_kms`, `AWS_KMS_KEY_ID` |
| `app/services/storage.py` | `s3:PutObject/GetObject/DeleteObject`, presign | `S3_BUCKET_NAME`, `S3_SSE_ALGORITHM` |
| `app/services/storage.py` (SSE-KMS) | `kms:GenerateDataKey`, `kms:Decrypt` via S3 | `S3_SSE_ALGORITHM=aws:kms`, `S3_KMS_KEY_ID` |

Production config already fails closed: `QR_KMS_MODE` must be `aws_kms`,
`REPORT_STORAGE_PROVIDER` must be `s3`, and `S3_KMS_KEY_ID` is required whenever
`S3_SSE_ALGORITHM=aws:kms` (`app/core/config.py`).

## Artifacts

| File | Purpose |
|---|---|
| `ops/iam/fitness-os-app-policy.json` | Least-privilege identity policy for the app principal |
| `ops/iam/fitness-os-kms-key-policy.json` | CMK key policy — app may use, never administer |
| `backend/scripts/kms_iam_verify.py` | Executable proof; exits 2 (`NOT VERIFIED`) without credentials |

Both policies carry `ACCOUNT_ID` / `REGION` / `REPORT_BUCKET` / key-id
placeholders. They are templates, not applied state.

## Setup

1. **Create two CMKs**, both with automatic rotation enabled:
   - `alias/fitness-os-qr` — QR HMAC envelope keys
   - `alias/fitness-os-reports` — S3 report bucket SSE-KMS
2. **Apply the key policy** (`ops/iam/fitness-os-kms-key-policy.json`) to the QR
   CMK with `APP_ROLE_NAME` / `ADMIN_ROLE_NAME` substituted. The deny statement
   is the point: the application must not be able to schedule deletion or turn
   rotation off.
3. **Attach the identity policy** (`ops/iam/fitness-os-app-policy.json`) to the
   application role.
4. **Bucket hardening** — block all public access, enforce
   `aws:SecureTransport`, default encryption `aws:kms` with the reports CMK, and
   a lifecycle rule matching the report retention window.
5. **Verify:**
   ```bash
   export AWS_REGION=... AWS_KMS_KEY_ID=alias/fitness-os-qr
   export S3_BUCKET_NAME=... S3_KMS_KEY_ID=alias/fitness-os-reports
   cd backend && ./.venv/bin/python scripts/kms_iam_verify.py
   ```
   Only `ALL PASS` closes P2-3-IAM. Exit code 2 means "not verified" and must
   never be recorded as a pass.

## Rotation

| Item | Cadence | Mechanism |
|---|---|---|
| CMK material | annual | AWS automatic key rotation (asserted by the verify script) |
| QR HMAC data keys | per secret | Envelope keys are minted per reference; rotating means re-issuing refs |
| App role credentials | 90 days | Prefer instance/task roles — no long-lived access keys |
| Verification | quarterly + after any IAM change | Re-run `kms_iam_verify.py`, record the output here |

Rotating the CMK does **not** invalidate existing `kms:enc:` references — AWS
keeps prior key material for decrypt. Disabling or deleting the CMK **does**,
and every QR secret bound to it becomes unresolvable. That is why the key policy
denies the application `ScheduleKeyDeletion` and `DisableKey`.

## Verification log

| Date | Runner | Result |
|---|---|---|
| — | — | **Never run against real AWS.** |

Append a row only from actual script output. Do not fill this table from
intent, from a plan, or from a staging dry-run that skipped steps.
