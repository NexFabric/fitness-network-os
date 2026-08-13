# Remaining Work Board

**Date:** 2026-08-10  
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
| Report object storage | 🟢 PR #55 — S3 upload + SSE + tenant-bound presigned URL + cleanup; CI/CodeQL verified, review/merge pending |
| /live /ready /metrics | 🟢 present |
| Public metrics honesty | 🟢 landed |
| Public-site CI job | 🟢 added |
| Privileged MFA enrollment | 🟢 PR #55 — restricted setup, TOTP UX and post-enrollment session rotation; CI/CodeQL verified, review/merge pending |
| Scanner offline deny-by-default | 🟢 landed |
| Scanner device auth | 🟢 landed — credentials **+ HMAC request signing + single-use nonce** (ADR-044) |
| Playwright E2E | 🟢 required GitHub CI gate; 36/36 real-browser scenarios passed in run `31702800041` |
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
| P2-1 | `/live`, `/ready` (503) and metrics endpoint foundation (superseded by PR #55 real counters) |
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
| P0-1 | Main Unit & Integration CI green at `c015748` (GitHub Actions run `31676689167`) |
| P1-3b | Real S3/MinIO upload, server-side encryption, tenant-key validation, short-lived presigned downloads and bounded cleanup implemented; PR #55 CI + CodeQL verified, review/merge pending |
| P1-4 | Privileged password login is restricted to MFA setup until TOTP enrollment succeeds; admin enrollment UX and session rotation implemented; PR #55 CI + CodeQL verified, review/merge pending |
| P1-7 | Playwright suite wired into `all-green`; 36/36 passed on PR #55 |
| P1-PKG | Frozen `uv.lock`, pinned `uv`, base-image digest, `.dockerignore`, non-root runtime and HEALTHCHECK; image build added to CI |

---

## Still open (cannot fake “complete”)

| ID | Item | Owner |
|----|------|-------|
| P1-10 | Actual restore drill evidence | A-OPS |
| P1-11 | ASVS/pentest + independent APPROVE | A-OPS + human |
| P2-3 | KMS QR secrets | A-QR |
| P2-OBS | Prometheus request/dependency/outbox metrics landed in PR #55; scraper/dashboard, traces and alert rules remain | A-OPS |

---

## Explicit non-claims

- Do **not** claim production-ready YES or Phase 26 PASS.  
- Do **not** redesign multitenancy.  
- Independent human APPROVE is **not** automated by this board.
