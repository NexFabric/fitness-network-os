# Remaining Work Board

**Date:** 2026-08-10  
**Program:** Phase 27 — Final Production Closure  
**Production-ready?** **NO** (architecture strong; evidence gates + full main CI still open)  
**Phase 26 PASS?** **NO / NOT VERIFIED**

---

## Snapshot

| Band | Verdict |
|------|---------|
| Architecture / tenancy / finance / outbox / QR core | 🟢 GO |
| CSRF bootstrap + cookie admin (local) | 🟢 landed |
| Production fail-closed config | 🟢 landed |
| Notification PII / prod mock block | 🟢 landed |
| Report local artifact (file://) | 🟢 improved (not S3 signed URL) |
| /live /ready /metrics | 🟢 present |
| Public metrics honesty | 🟢 landed |
| Public-site CI job | 🟢 added |
| MFA enrollment enforcement (code gate) | 🟡 partial (no full TOTP UX) |
| Scanner offline deny-by-default | 🟢 landed |
| Scanner device auth | 🟢 landed — credentials **+ HMAC request signing + single-use nonce** (ADR-044) |
| Playwright E2E | 🟢 landed (21 tests, real Chromium + real backend) |
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
| P1-3 | Report writes real CSV under REPORT_STORAGE_DIR |
| P1-8 | CI job `public-site` build |
| P1-9 | Marketing design targets (not fake live stats) |
| P1-2 | Scanner offline deny-by-default |
| P2-1 | /live, /ready (503), /metrics stub |
| P1-4 | MFA: refuse login without code if MFA enrolled |
| P1-10/11 | Honest UNVERIFIED status docs under `docs/ops/` |
| P1-12 | FE builds as **required** branch checks (via `all-green` job) |
| SEC-1 | Dependabot high alert triage (npm audit fix vite/esbuild) |
| P1-1 | Scanner **device** authentication |
| P1-4b | Real TOTP + privileged role matrix UI (Backend) |
| P1-7 | Playwright browser E2E suite (21 tests, real Chromium + real backend) |
| SEC-2 | Device channel HMAC signing + nonce replay protection (ADR-044) |

---

## Still open (cannot fake “complete”)

| ID | Item | Owner |
|----|------|-------|
| P0-1 | GitHub main required Unit & Integration green on push | A-CI / ORCH |
| PR #49 | Merge blocked: `main` needs 1 approving review, `enforce_admins` on — author cannot self-approve | human |
| P1-3b | Signed object-storage URLs + encryption | A-RPT |
| P1-10 | Actual restore drill evidence | A-OPS |
| P1-11 | ASVS/pentest + independent APPROVE | A-OPS + human |
| P2-2 | Redis distributed rate limit | A-CFG |
| P2-3 | KMS QR secrets | A-QR |

---

## Explicit non-claims

- Do **not** claim production-ready YES or Phase 26 PASS.  
- Do **not** redesign multitenancy.  
- Independent human APPROVE is **not** automated by this board.
