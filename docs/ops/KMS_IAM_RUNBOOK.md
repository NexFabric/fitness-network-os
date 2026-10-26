# KMS / IAM Runbook — P2-3-IAM

**Date:** 2026-08-16 · **Status:** **UNVERIFIED**

Index: `docs/ops/EXTERNAL_GATES.md`. The policies, this runbook and the
verification script are in the repo. **Nothing has been executed against
a real AWS account** from this machine. P2-3-IAM stays open until
`ops/iam/apply_and_verify.sh` prints `ALL PASS` against a real CMK and
an operator pastes that log below.

## Close this gate (one command)

Owner: **A-OPS**. Requires a production (or dedicated staging) AWS
account, two CMKs, and an application role.

```bash
export AWS_REGION=eu-central-1
export ACCOUNT_ID=123456789012
export APP_ROLE_NAME=fitness-os-app
export ADMIN_ROLE_NAME=fitness-os-admin
export QR_CMK_KEY_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   # key id, not alias
export S3_CMK_KEY_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
export REPORT_BUCKET=fitness-os-reports-prod
export AWS_KMS_KEY_ID=alias/fitness-os-qr
export S3_BUCKET_NAME="$REPORT_BUCKET"
export S3_KMS_KEY_ID=alias/fitness-os-reports
export CONFIRM_APPLY=yes          # omit to print substituted policy only
./ops/iam/apply_and_verify.sh
```

Exit 2 = `NOT VERIFIED` (no credentials, leftover placeholders, or
`CONFIRM_APPLY` unset). Do not record exit 2 as a pass.

Without `CONFIRM_APPLY=yes` the script only substitutes and lint-checks
the templates. Create the two aliases and the roles **before** applying;
the script will not invent a CMK.

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
| `ops/iam/apply_and_verify.sh` | Substitute → optional apply → `kms_iam_verify.py` |
| `backend/scripts/kms_iam_verify.py` | Executable proof; exits 2 without credentials |

Both policies carry `ACCOUNT_ID` / `REGION` / `REPORT_BUCKET` / key-id
placeholders. They are templates, not applied state. The apply script
refuses to send a document that still contains a placeholder.

## Setup (once per account)

1. **Create two CMKs**, both with automatic rotation enabled:
   - `alias/fitness-os-qr` — QR HMAC envelope keys
   - `alias/fitness-os-reports` — S3 report bucket SSE-KMS
2. **Create the application role** (`APP_ROLE_NAME`) and an admin role
   that is allowed to administer the CMKs. Prefer instance/task roles —
   no long-lived access keys on the app.
3. Run the one-command block above with `CONFIRM_APPLY=yes`.
4. **Bucket hardening** is a separate gate (`ops/s3/apply_and_prove.sh`).
   Run it after the reports CMK exists.

The deny statement is the point: the application must not be able to
schedule deletion or turn rotation off. The verifier asserts that
`kms:ScheduleKeyDeletion` is denied.

## Rotation

| Item | Cadence | Mechanism |
|---|---|---|
| CMK material | annual | AWS automatic key rotation (asserted by the verify script) |
| QR HMAC data keys | per secret | Envelope keys are minted per reference; rotating means re-issuing refs |
| App role credentials | 90 days | Prefer instance/task roles — no long-lived access keys |
| Verification | quarterly + after any IAM change | Re-run `ops/iam/apply_and_verify.sh` without `CONFIRM_APPLY` (verify only) |

Rotating the CMK does **not** invalidate existing `kms:enc:` references — AWS
keeps prior key material for decrypt. Disabling or deleting the CMK **does**,
and every QR secret bound to it becomes unresolvable. That is why the key policy
denies the application `ScheduleKeyDeletion` and `DisableKey`.

## Verification log

| Date | Runner | Command output (ALL PASS / NOT VERIFIED) |
|---|---|---|
| — | — | **Never run against real AWS.** |

Append a row only from actual script output. Do not fill this table from
intent, from a plan, or from a staging dry-run that skipped steps.
