# Remaining Work Board

**Date:** 2026-08-16  
**Branch:** `feat/public-site-modernization-and-seo`  
**Alembic head:** `xf7a8b9c0d1e`  
**Program:** Phase 27–29 — in-repo closure  
**Production-ready?** **NO**  
**Phase 26 PASS?** **NO / NOT VERIFIED**

Authority checklist: `docs/PROGRESS_CHECKLIST.md`

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
| DR / pentest / real S3 / KMS IAM | 🔴 UNVERIFIED (external) |
| Independent APPROVE | 🔴 human |
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

Older closed IDs (P0/P1/WAVE/FED/B1) remain as in the 2026-08-13 snapshot; they are not re-listed.

---

## Still open — in-repo (doable)

| ID | Item | Owner |
|----|------|-------|
| HAND-1 | Human sign-off of `docs/ops/HAND1_BROWSER_PROOF.md` (Playwright covers invite / onboarding / portal bind / scanner pair / report link) | human |

## Still open — cannot fake “complete”

| ID | Item | Owner |
|----|------|-------|
| P1-3b-RT | S3/MinIO **runtime** proof — real bucket + credentials | A-OPS |
| P1-10 | Actual restore/PITR drill evidence | A-OPS |
| P1-11 | ASVS/pentest + independent APPROVE | A-OPS + human |
| P2-OBS | Scraper / dashboard / traces / alert rules | A-OPS |
| P2-3-IAM | Production KMS alias / IAM / rotation proof | A-OPS |
| ISO-1 | IsolationProvider — do not invent; keep abstraction | — |

GitHub Settings (2026-08-16, `gh` API): Default CodeQL Setup = **not-configured**. `main` required checks: Unit tests, FE builds, Frontend Images, Playwright, CodeQL, All Required Checks Passed. Reviews: 1 approval, dismiss stale, conversation resolution, enforce_admins, strict. `delete_branch_on_merge` + Dependabot security updates enabled.

---

## Explicit non-claims

- Do **not** claim production-ready YES or Phase 26 PASS.
- Do **not** redesign multitenancy.
- Independent human APPROVE is **not** automated by this board.
