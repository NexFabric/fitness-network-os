# Production AWS S3 artifacts

**Status:** **UNVERIFIED** · P1-3b-PROD

Index: `docs/ops/EXTERNAL_GATES.md`. MinIO 10/10 proof is
`docs/ops/S3_RUNTIME_PROOF.md` (P1-3b-RT). These files are the AWS
bucket contract. They have never been applied from this machine.

`backend/scripts/s3_runtime_proof.py` is the **MinIO** drill. It
expects `S3_ENDPOINT_URL` and `S3_SSE_ALGORITHM=AES256`. Do **not**
point it at production SSE-KMS and call that this gate.

## Close this gate (one command)

Owner: **A-OPS**.

```bash
export AWS_REGION=eu-central-1
export ACCOUNT_ID=123456789012
export APP_ROLE_NAME=fitness-os-app
export REPORT_BUCKET=fitness-os-reports-prod
export S3_KMS_KEY_ID=alias/fitness-os-reports   # or key ARN
export CONFIRM_APPLY=yes                        # omit to lint + print only
./ops/s3/apply_and_prove.sh
```

Then, with the **same** credentials as the application role:

```bash
export AWS_KMS_KEY_ID=alias/fitness-os-qr
export S3_BUCKET_NAME="$REPORT_BUCKET"
export S3_KMS_KEY_ID=alias/fitness-os-reports
cd backend && ./.venv/bin/python scripts/kms_iam_verify.py
```

P1-3b-PROD needs the apply script `ALL PASS` **and** the verifier's
`s3-sse-kms` step. Exit 2 is `NOT VERIFIED`.

## Templates

| File | Purpose |
|---|---|
| `bucket-policy.json` | Deny non-TLS; deny unencrypted PutObject; allow the app role only |
| `public-access-block.json` | All four Block Public Access flags |
| `lifecycle.json` | Expire leftover `reports/` objects at 90 days |
| `bucket-encryption.json` | Default encryption `aws:kms` + bucket key |
| `apply_and_prove.sh` | Substitute → apply → assert via AWS API |

Apply only from an operator session with the production account.
Paste the script log into the evidence table below — do not invent a
row.

## Evidence log

| Date | Runner | Bucket | Result |
|---|---|---|---|
| — | — | — | **Never applied to real AWS.** |
