# Remaining Work Board

**Date:** 2026-08-13 (post PR #57 merge, `main` = `837cec4`)  
**Program:** Phase 27 — Final Production Closure  
**Production-ready?** **NO** (architecture strong; external evidence gates still open)
**Phase 26 PASS?** **NO / NOT VERIFIED**

---

## Snapshot

| Band | Verdict |
|------|---------|
| Architecture / tenancy / finance / outbox / QR core | 🟢 GO |
| CSRF bootstrap + cookie admin (local) | 🟢 landed |
| Production fail-closed config | 🟢 landed |
| Notification PII / prod mock block | 🟢 landed |
| Report object storage | 🟢 merged (PR #55) — S3 upload + SSE + tenant-bound presigned URL + cleanup; **runtime proof against a real bucket still open (P1-3b)** |
| /live /ready /metrics | 🟢 present |
| Public metrics honesty | 🟢 landed |
| Public-site CI job | 🟢 added |
| Privileged MFA enrollment | 🟢 merged (PR #55) — restricted setup session, TOTP UX and post-enrollment session rotation |
| Scanner offline deny-by-default | 🟢 landed |
| Scanner device auth | 🟢 landed — credentials **+ HMAC request signing + single-use nonce** (ADR-044) |
| Playwright E2E | 🟢 required GitHub CI gate; 36/36 real-browser scenarios passed in run `31732326181` |
| DR / pentest evidence | 🔴 UNVERIFIED (docs only) |
| Independent APPROVE | 🔴 human |
| Public launch | 🔴 **NO-GO** |

---

## Closed this session (code)

| ID | Item |
|----|------|
| P0-2 | CSRF `GET /auth/csrf` + admin/scanner ensureCsrf |
| P0-3 | Cookie-only admin session (tenant in localStorage only) |
| P0-4 | Truth docs NO production-ready |
| P1-5 | `Settings.validate_production()` fail-closed |
| P1-6 | No recipient PII in logs; prod blocks mock SMS/WA/PUSH |
| P1-3 | Initial local CSV artifact path (superseded by P1-3b object storage closure) |
| P1-8 | CI job `public-site` build |
| P1-9 | Marketing design targets (not fake live stats) |
| P1-2 | Scanner offline deny-by-default |
| P2-1 | `/live`, `/ready` (503) and metrics endpoint foundation (superseded by real counters merged in PR #55) |
| P1-4 | MFA: refuse login without code if MFA enrolled |
| P1-10/11 | Honest UNVERIFIED status docs under `docs/ops/` |
| P1-12 | FE builds as **required** branch checks (via `all-green` job) |
| SEC-1 | Dependabot high alert triage (npm audit fix vite/esbuild) |
| P1-1 | Scanner **device** authentication |
| P1-4b | Real TOTP + privileged role matrix UI (Backend) |
| P1-7 | Playwright browser E2E suite (21 tests, real Chromium + real backend) |
| SEC-2 | Device channel HMAC signing + nonce replay protection (ADR-044) |
| P2-2 | Redis-backed distributed rate limit (login), fail-open with degraded log |
| API-1 | Plan catalogue (`/plans`, versions, publish) + membership creation (`POST /memberships`) — the lifecycle surface can now be driven end to end |
| API-2 | Delivery and run history endpoints (`GET /notifications/deliveries`, `GET /reports/runs`) — bounded, filterable |
| SEC-3 | Dead `verify_idempotency_key` middleware removed — it advertised idempotency while only checking header presence; the real path is `api/idempotency_uow.py` |
| P0-1 | Main Unit & Integration CI green at `837cec4` — 325 passed · 1 skipped (GitHub Actions run `31732326181`) |
| P1-3b | Real S3/MinIO upload, server-side encryption, tenant-key validation, short-lived presigned downloads and bounded cleanup **implemented and merged**. Code path is closed; runtime proof against a real bucket is still open below. |
| P1-4 | Privileged password login is restricted to MFA setup until TOTP enrollment succeeds; admin enrollment UX and session rotation merged |
| P1-7 | Playwright suite wired into `all-green`; 36/36 passed, merged |
| P1-PKG | Frozen `uv.lock`, pinned `uv`, base-image digest, `.dockerignore`, non-root runtime and HEALTHCHECK; image build added to CI |
| P1-USER | `POST /staff/accounts` creates a login and links it to the tenant in one transaction, returning a one-time password once. `must_change_password` plus a restricted `password_reset` session force rotation before the account can be used, and `resolve_auth_level()` orders enrollment ahead of rotation so finishing MFA can no longer skip it (PR #57) |
| WAVE-1 | Legal pages (`/privacy`, `/terms`, `/kvkk`), Backend `/me` self-service expansion (`/invoices`, `/payments`, `/consents`, `finance:read:self`), 5-tab MemberPortal UI |
| WAVE-2 | Forensic Access Snapshot (`AccessAttempt.snapshot_data`), Front Desk Reception workspace (`/reception`, instant search, manual override checkin), Server-side KPI Engine (`GET /dashboard/kpis`) |
| WAVE-3 | CSV Data Migration Pipeline (`DataImportBatch`, `DataImportRow`, `DataImport.tsx`), Payment Attempts & Dunning policy (`PaymentAttempt`, `DunningPolicy`, invoice retry columns), Tenant Onboarding state machine (`TenantOnboarding`) |
| FED-HQ | 6-tab Federation HQ Console (`SuperAdminPortal.tsx`), Gym Lifecycle (`create_tenant`, `suspend_tenant`, `reactivate_tenant`), Roaming Passport Matrix (`PassportConfig`), Compliance & Audit Registry (`ComplianceRecord`), Network Alert Broadcasts (`NetworkAlert`), Cross-Tenant Analytics (`AnalyticsOverview`), Alembic migration `x9c0d1e2f3a4` |
| P2-3 | AWS KMS envelope encryption (`kms:enc:`) with `GenerateDataKey` & `Decrypt`, fail-closed boot validation in `core/config.py` |
| MILESTONE-B1 | Group Class & PT Booking Engine: 6 RLS tables (`class_types`, `class_schedules`, `class_sessions`, `class_bookings`, `trainer_availabilities`, `pt_appointments`), Alembic `xa2b3c4d5e6f`, `SELECT ... FOR UPDATE` write lock concurrency, monotonic FIFO waitlist auto-promotion, Admin Visual Calendar & Attendee Roster Drawer (`Classes.tsx`), Trainer Portal live attendance ledger (`TrainerPortal.tsx`), 6-tab Member Portal (`MemberPortal.tsx`), real PostgreSQL concurrency pytest suite, and Playwright E2E suite (`classes_and_booking_flows.spec.ts`) |

---

## Still open (cannot fake “complete”)

| ID | Item | Owner |
|----|------|-------|
| P1-3b-RT | S3/MinIO **runtime** proof — real bucket + credentials in staging; the adapter is merged but has never written to a live bucket | A-OPS |
| P1-10 | Actual restore/PITR drill evidence | A-OPS |
| P1-11 | ASVS/pentest + independent APPROVE | A-OPS + human |
| P2-OBS | Prometheus request/dependency/outbox metrics merged; scraper/dashboard, traces and alert rules remain as external infra | A-OPS |

---

## Explicit non-claims

- Do **not** claim production-ready YES or Phase 26 PASS.  
- Do **not** redesign multitenancy.  
- Independent human APPROVE is **not** automated by this board.
