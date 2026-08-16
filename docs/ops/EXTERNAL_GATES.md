# External gates — operator index

These gates cannot be closed from this repository alone. Every row is
**UNVERIFIED**. Filling a packet, attaching a template, or running a
local drill does **not** change that. Do not write PASS, VERIFIED, or
Phase 26 GO here.

In-repo certification that *supports* these gates already landed
(#89–#96, tip `48b3c79`). Do not re-implement packets, verifiers, or
compose TLS. See `docs/CAMPAIGN_REGISTER.md`. Local MinIO / local PITR /
null-receiver drills are **not** the rows below.

| gate | status | command or file | owner |
|---|---|---|---|
| Independent pentest (P1-11) | UNVERIFIED | `docs/ops/PENTEST_BRIEF.md` | human |
| AWS KMS / IAM (P2-3-IAM) | UNVERIFIED | `ops/iam/apply_and_verify.sh` | A-OPS |
| AWS S3 (P1-3b-PROD) | UNVERIFIED | `ops/s3/apply_and_prove.sh` | A-OPS |
| Off-host WAL / RPO (P1-10-PROD) | UNVERIFIED | `ops/wal/prod_rpo.sh` | A-OPS |
| Real pager (P2-OBS-PROD) | UNVERIFIED | `ops/observability/pager_prove.sh` | A-OPS |
| HAND-1 browser signature | UNVERIFIED | `docs/ops/HAND1_BROWSER_PROOF.md` | human |
| KVKK / legal | UNVERIFIED | `docs/ops/LEGAL_APPROVAL.md` | human |
| Live HA | UNVERIFIED | `ops/ha/live_check.sh` | A-OPS |

A command that exits 2 printed `NOT VERIFIED`. That is the honest
default when credentials, a live host, or a human acknowledgement are
missing. A command that prints `ALL PASS` is evidence for the matching
packet — it still does not flip the row above. An operator records the
log in that packet; an agent does not.

Related self-assessments (not these gates):
`docs/ops/ASVS_L2_COMPLIANCE_REPORT.md`,
`docs/ops/S3_RUNTIME_PROOF.md` (MinIO),
`docs/ops/DR_RESTORE_STATUS.md` (local PITR),
`docs/ops/OBSERVABILITY.md` (null-receiver drill).
