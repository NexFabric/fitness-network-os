# Remaining Work Board

**Date:** 2026-08-16  
**Branch:** `main`  
**Last code:** `1b42ab4` (PR **#89** / **#91** / **#93** / **#94** MERGED)  
**Alembic head:** `xi0d1e2f3a4b`  
**Merged 2026-08-16:** `#62`→`ae6267d` (Phase 29 + RC) · `#78`→`fb3a26d` (ops drills) · `#80`→`d56b6a0` (dependency batch + HAND-1 + dependabot scope) · `#83`/`#84` · `#64/#66/#68` (CI actions) · `#89`→`e05e29f` · `#91`→`27fff12` · `#93`→`d9a5c9d` · `#94`→`1b42ab4`  
**Campaign landings:** **#89–#94 MERGED** — migrate gate · migrator isolation · TLS · ops-drills PITR (CI `31968740247` SUCCESS on `1b42ab4`) · coverage floors · Safety CLI dropped · release-truth checker. **Do not redo** — `docs/CAMPAIGN_REGISTER.md`. EXTERNAL_GATES **UNVERIFIED**.  
**CI:** every merge passed required CI. Merge gate is CI only (review requirement removed 2026-08-16, single maintainer).  
**Program:** Phase 27–29 + RC closure  
**Production-ready?** **NO**  
**Phase 26 PASS?** **NO / NOT VERIFIED**

Authority checklist: `docs/PROGRESS_CHECKLIST.md`  
Do-not-redo register: `docs/CAMPAIGN_REGISTER.md`

---

## Snapshot

| Band | Verdict |
|------|---------|
| Architecture / tenancy / finance / outbox / QR core | 🟢 GO |
| CSRF + cookie admin + privileged MFA + step-up + idle | 🟢 landed (this branch) |
| Device HMAC at rest (`fernet:hmac:`) + scanner pairing UI | 🟢 landed (this branch) |
| Member portal bind + staff email hook + compose workers | 🟢 landed (this branch) |
| Playwright E2E | 🟢 required CI gate |
| Invite token + onboarding wizard UI | 🟢 landed (this branch) |
| DR restore + PITR drills | 🟢 executed 2026-08-16 (local container) |
| S3 report storage against a real S3 API | 🟢 10/10 (MinIO) — AWS bucket/IAM still open |
| Metrics → scrape → alert → dashboard | 🟢 landed + alert path drilled |
| Pentest / production AWS bucket / KMS IAM | 🔴 UNVERIFIED (external) |
| Independent **security** APPROVE (P1-11 / Phase 26) — not the merge gate | 🔴 human |
| Public launch | 🔴 **NO-GO** |

---

## Closed on this branch (Phase 29)

| ID | Item |
|----|------|
| BOLA-1 | `reception:read` + reception/import/PT/dashboard assignment scope |
| MFA-1 | Privileged MFA set includes FRONT_DESK; dummy Argon2 timing |
| STAFF-1 | Staff `UserRole` `STAFF`→`FRONT_DESK` |
| CSV-1 | CSV formula/size caps; `+90…` phones allowed |
| DEV-1 | Device signing material `fernet:hmac:` at rest |
| STEP-1 | Step-up MFA 5 min on sensitive writes |
| IDLE-1 | Privileged idle 30 min → `401 session_idle` |
| BG-1 | Superuser tenant writes `403 break_glass_required` |
| SMTP-1 | SMTP sends `delivery.body` |
| CSP-1 | `'unsafe-eval'` removed from admin + scanner CSP |
| SCAN-1 | Scanner pairs via device auth; demo password gone |
| PORT-1 | `POST /members/{id}/portal-account` + Members.tsx |
| MAIL-1 | Staff create → `schedule_delivery` EMAIL |
| WRK-1 | Compose notification + outbox workers; Dockerfile `uv.lock` |
| RLS-G | Growth leads RLS test is real PostgreSQL |
| INVITE-1 | `account_invites` hashed token + `POST /auth/invite/accept` + `/invite` |
| ONB-UI | Admin `/onboarding` wizard |
| INVITE-OTP | Standing OTP no longer returned or emailed |
| COV-1a | eslint in required FE jobs; pytest `--cov` report |
| DSAR-1a | Bound-member export + `dsar_requests` ledger |
| DSAR-1b | Erasure anonymize; open invoices 409 hold; paid invoices stay |
| GOD-1 | Split SuperAdmin / Classes / MemberPortal tab shells |
| GROW-F | Growth CRM frozen schema-only — no API, no table drop |
| IMG-1 | Frontend Dockerfiles use workspace lockfile + SPA nginx; prod compose has ENCRYPTION_KEY + admin/scanner images |
| MIG-1 | Dev compose `migrate` one-shot before API/workers |
| COV-1b | Measured 72%; CI `--cov-fail-under=70` |
| IDX-1 | Model/DB index alignment (`xf7a8b9c0d1e`) so `alembic check` can pass |
| STAFF-2 | Staff list returns `email`; class/PT picker uses tenant-isolated `GET /classes/trainers` (UserRole TRAINER mapping, not `first_name`); seed writes trainer/desk `staff` rows |
| UR-1 | Partial unique grants on `user_roles` (`xg8b9c0d1e2f`) |
| BK-ERR | `booking.py` raises `BookingError`; DSAR swallows only not-found/conflict |
| TR-FK | Composite FK `(tenant_id, trainer_user_id) → staff`; picker requires staff + active |
| PT-EX | `btree_gist` EXCLUDE on confirmed PT overlaps |
| TZ-1 | `generate_sessions` uses `Location.timezone`; unique schedule+start |
| KPI-1 | Dashboard member KPIs use `visible_member_ids` |
| MEM-T | Membership mutations pin `tenant_id`; class book honors `required_entitlement_type` |

Older closed IDs (P0/P1/WAVE/FED/B1) remain as in the 2026-08-13 snapshot; they are not re-listed.

---

## Closed this campaign (2026-08-16) — do not reopen

| ID | Item |
|----|------|
| CERT-89 | PR **#89** `e05e29f` — production certification squash |
| TRUTH-91 | PR **#91** `27fff12` — authority docs mark #89 MERGED |
| REL-TRUTH | PR **#93** `d9a5c9d` — `check_release_truth.py` forbids stale OPEN vs MERGED |
| TLS-PROOF | PR **#94** `1b42ab4` — host chown 999:999 + encrypt-only SSL context |
| SAFETY-1 | Safety CLI removed from required CI; pip-audit is the SCA gate |
| DRILLS-CI | ops-drills dump/restore + PITR green on tip (`31968740247` @ `1b42ab4`) |
| REV-62 | Owner decision: review requirement removed; CI is the merge gate |
| MIG-PROD | Prod compose migrate-before-app |
| TLS-1 | Production DB/Redis TLS or `PRODUCTION_PRIVATE_NETWORK=1` |
| CORS-HTTPS | Production CORS origins must be `https://` |
| CD-1 | Compose-first deploy choreography + `workflow_dispatch` (live promote UNVERIFIED) |
| COV-CRIT | Critical-module coverage floors (anti-regression, measured) |
| PERF-1 | k6 harness landed (not a claimed SLO) |
| A11Y-1 | axe Playwright regression spec (color-contrast disabled — known dark teal) |
| MIG-SEC | Migrator DSN only on `COMPONENT_NAME=migrate` |

---

## Still open — in-repo (doable)

| ID | Item | Owner |
|----|------|-------|
| CI-62 | Historical: `ab860f0` `31947417828` SUCCESS. Later SHAs ride required CI on merge. Do not re-claim. | — |
| PR-95 | P1 test-depth (`feat/p1-critical-test-depth`). Rebase + required CI. **Do not open a sibling.** | one agent |
| PR-92 | Dependabot github-actions. Merge only when up to date with `main` and All Green. | one agent |
| HAND-1 | Human sign-off of `docs/ops/HAND1_BROWSER_PROOF.md`. Signature table is empty. **Do not agent-sign.** | human |

## Still open — cannot fake “complete”

| ID | Item | Owner |
|----|------|-------|
| ~~P1-3b-RT~~ | **Closed 2026-08-16** — 10/10 against a real S3 API (MinIO) with the actual provider. `docs/ops/S3_RUNTIME_PROOF.md` | — |
| ~~P1-10~~ | **Closed 2026-08-16** — dump/restore **and** PITR drill both passed. `docs/ops/DR_RESTORE_STATUS.md` | — |
| ~~P2-OBS~~ | **Closed 2026-08-16** — Prometheus/Alertmanager/Grafana + 7 rules + drilled alert path. `docs/ops/OBSERVABILITY.md` | — |
| P1-11 | ASVS/pentest by an independent third party | A-OPS + human |
| P2-3-IAM | Production KMS alias / IAM / rotation. Artifacts + verifier landed; **never run against real AWS** | A-OPS |
| P1-3b-PROD | Real **AWS** bucket + policy + public-access block + SSE-KMS | A-OPS |
| P1-10-PROD | Off-host continuous WAL archiving + RPO measured on the production host | A-OPS |
| P2-OBS-PROD | Real Alertmanager receiver from a secret + distributed tracing | A-OPS |
| HAND-1 | Human sign-off of the browser proof | human |
| ISO-1 | IsolationProvider — do not invent; keep abstraction | — |

GitHub Settings (2026-08-16, `gh` API): Default CodeQL Setup = **not-configured**. `main` required checks: Unit tests, FE builds, Frontend Images, Playwright, CodeQL, All Required Checks Passed. **No review requirement** (removed 2026-08-16, single maintainer); conversation resolution, `enforce_admins`, `strict` still on. `delete_branch_on_merge` + Dependabot security updates enabled.

---

## Explicit non-claims

- Do **not** claim production-ready YES or Phase 26 PASS.
- Do **not** redesign multitenancy.
- Do **not** re-implement any ID in **Closed this campaign**.
- Do **not** merge PR **#86** (React 19).
- Independent human APPROVE is **not** automated by this board.
