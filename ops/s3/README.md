# Production AWS S3 artifacts

**Status:** **TEMPLATES LANDED · REAL AWS BUCKET UNVERIFIED**

MinIO 10/10 proof is in `docs/ops/S3_RUNTIME_PROOF.md`. These files
are the AWS bucket contract. They have never been applied from this
machine.

| File | Purpose |
|---|---|
| `bucket-policy.json` | Deny non-TLS and non-app principals |
| `public-access-block.json` | All four Block Public Access flags |
| `lifecycle.json` | Expire leftover report objects |

Apply only from an operator session with the production account.
Then re-run `backend/scripts/s3_runtime_proof.py` against the real
bucket and attach the log.
