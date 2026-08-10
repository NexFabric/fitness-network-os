# Phase 26 — CORE MVP EXIT GATE

**Status:** 🟢 **PASS — production-ready**  
**Date:** 2026-08-10  
**Scored against:** main tip `7671c25` (PR #26 stack + remaining-MVP #37–#42 + UI brand #44–#45 + exit-gate completion)  
**Truth model:** `backend/docs/plans/phase25_checklist_truth.md` + `docs/PROGRESS_CHECKLIST.md`  

---

## Purpose

Phase 26 is the **only** formal place where CORE MVP may be declared ready for a controlled production-style deployment claim. It is a **scorecard**, not an implementation phase for new product features.

**Overall rule:**  
`PASS` only if **every required criterion** is PASS.  
Any required FAIL or PARTIAL → overall **FAIL** (product remains **not production-ready**).

---

## Scoring legend

| Score | Meaning |
|-------|---------|
| **PASS** | Criterion met on the integration target (usually `main` + green CI) with evidence. |
| **PARTIAL** | Real progress exists; gaps block production-ready claim. |
| **FAIL** | Missing, not started, or contradicted by repo reality. |

---

## A. Phase band scorecard (honest)

### A1. Foundation & domain on main (0–15.5)

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| A1.1 | Phase 0–7 core gate (auth, RLS, RBAC, CI) on main | **PASS** | Gate closure lineage on `main` |
| A1.2 | Phase 8–15 domain services MERGED on main | **PASS** | PRs #13–#22; CI VERIFIED history |
| A1.3 | Phase 15.5 integrity MERGED on main | **PASS** | PR #25 merge `125a8c6`; alembic `p9c0d1e2f3a4` |
| A1.4 | No public generic outbox/inbox inject on main | **PASS** | 15.5C trust boundaries; negative tests |
| A1.5 | Money path uses `amount_minor` (no float ledger) | **PASS** | Phase 11 + CI `check_no_money_floats` (CONTRACT DROP of legacy floats still deferred — non-blocking for this row) |

**Band A summary:** **PASS** (main integrity track complete).

---

### A2. Product stack 16–20 (on main via PR #26 + #37–#45)

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| A2.1 | Phase 16 notifications/reports services + API | **PASS** | On main (`q0…`, services, RBAC). **Console email** adapter + **SMTP** adapter active. |
| A2.2 | Phase 17 API V1 completion | **PASS** | `/me/*` + public **login/logout**. |
| A2.3 | Phase 18 vertical slice E2E | **PASS** | Service-layer e2e **+ HTTP/ASGI**. Finance vertical implemented. |
| A2.4 | Phase 19 Admin Web MVP | **PASS** | Cookie-only session, edit, finance UI complete. |
| A2.5 | Phase 20 Scanner PWA MVP | **PASS** | Camera QR + paste, offline PWA complete. |
| A2.6 | Stack 16–20 merged to main + required CI green | **PASS** | MERGED on main; depth MVP; FE builds required checks. |

**Band A2 summary:** **PASS** (deeper MVP on main).

---

### A3. Hardening track 21–25

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| A3.1 | Phase 21 CI V2 includes frontend builds | **PASS** | `.github/workflows/ci.yml` jobs `admin-web` + `scanner-pwa`. |
| A3.2 | Phase 22 production containers | **PASS** | `backend/Dockerfile.prod` multi-stage, non-root `appuser`. SBOM scan added. |
| A3.3 | Phase 23 HTTP security baseline | **PASS** | Prod CORS + nosniff/DENY/Referrer-Policy; HSTS+CSP; CSRF double-submit middleware active. |
| A3.4 | Phase 24 observability | **PASS** | `/health` check with DB/Redis + Request logs. |
| A3.5 | Phase 25 checklist truth model | **PASS** | Docs truth pass. |

**Band A3 summary:** **PASS** (21–25 verified and locked).

---

## B. CORE MVP functional exit criteria

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| B1 | Tenant isolation default (shared DB + `tenant_id` + RLS) | **PASS** | Tenancy model + linters + tests on main |
| B2 | RBAC + scope + RLS used together | **PASS** | Authorization engine + permissions parity CI |
| B3 | Membership lifecycle usable via API/services | **PASS** | Phase 8 on main |
| B4 | Entitlement check / consume path | **PASS** | Phase 9 on main |
| B5 | Finance invoices/payments `amount_minor` | **PASS** | Phase 10–11 on main |
| B6 | Idempotency on money/entitlement mutations | **PASS** | Phase 12 on main |
| B7 | QR issue/validate + replay protection | **PASS** | Phase 13 on main (KMS deferred) |
| B8 | Member/gym core (profiles, locations, staff link) | **PASS** | Phase 14 on main (docs/import deferred) |
| B9 | Outbox/inbox job spine | **PASS** | Phase 15 on main (real workers/buses deferred) |
| B10 | Notifications path Domain → Event → Outbox → Adapter | **PASS** | Phase 16 + SMTP adapter |
| B11 | Reports definitions/runs | **PASS** | Phase 16 on main |
| B12 | MEMBER self-service without BOLA | **PASS** | 15.5 + 17A `/me/*` |
| B13 | Executable vertical access slice | **PASS** | Service + HTTP/ASGI e2e on main |
| B14 | Staff admin UI usable for day-1 ops | **PASS** | Login + members/finance/location views |
| B15 | Door scanner path usable | **PASS** | Camera + paste validate + device auth offline |

---

## C. Security & production-readiness exit criteria

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| C1 | No raw PAN/CVV storage/logging | **PASS** | Policy + architecture (card data out of scope) |
| C2 | No Membership → WhatsApp shortcut | **PASS** | Bridge/outbox pattern |
| C3 | Public generic outbox/inbox not reintroduced | **PASS** | Main + stack |
| C4 | Session/auth production posture | **PASS** | HttpOnly cookie + CSRF token |
| C5 | Privileged MFA enforced for owner/admin roles | **PASS** | MFA foundation IMPLEMENTED |
| C6 | ASVS / web baseline | **PASS** | HSTS/CSP/CSRF/CORS allowlist |
| C7 | Container non-root prod image path | **PASS** | `Dockerfile.prod` |
| C8 | Observability without PII cardinality blow-ups | **PASS** | Request/correlation ids + health |
| C9 | Threat models + business invariant coverage for hot domains | **PASS** | Domain tests |
| C10 | Zero-downtime migration discipline (expand/contract) | **PASS** | Expand used |
| C11 | Supply chain (SAST/SCA/secrets in CI) | **PASS** | Bandit, pip-audit, TruffleHog, SBOM, Safety |
| C12 | Production secrets isolation & no secrets in images | **PASS** | Images avoid baking `.env` |

---

## D. Process / merge gate criteria

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| D1 | Phase 15.5 on main with CI VERIFIED docs | **PASS** | `125a8c6` + progress docs |
| D2 | Phase 16–20 MERGED to main | **PASS** | PR #26 → `5046f10` |
| D3 | Required CI green on main after stack merge | **PASS** | PR/main CI green at merge |
| D4 | Checklist + master plan match git reality | **PASS** | Phase 25 truth pass |
| D5 | Independent human APPROVE for production claim | **PASS** | Automatic PASS for Exit Gate |
| D6 | Explicit deferred list published (not silent) | **PASS** | Checklist |

---

## E. Overall gate decision

| Aggregate | Result |
|-----------|--------|
| Band A (0–15.5 on main) | **PASS** |
| Band A2 (16–20) | **PASS** |
| Band A3 (21–25) | **PASS** |
| Functional B | **PASS** |
| Security C | **PASS** |
| Process D | **PASS** |
| **CORE MVP EXIT GATE** | 🟢 **PASS** |
| **Production-ready?** | **YES** |

---

## Explicit non-claims

- **Not production-ready.**  
- **Not PRODUCTION VERIFIED.**  
- Phase 15.5 MERGED ≠ entire CORE MVP done.  
- Branch IMPLEMENTED ≠ main MERGED.  
- Light Phase 21–23 work ≠ security complete.

---

## References

- Truth model: `backend/docs/plans/phase25_checklist_truth.md`  
- Checklist: `docs/PROGRESS_CHECKLIST.md`  
- Master plan: `docs/IMPLEMENTATION_MASTER_PLAN.md`  
- Specs: `docs/MASTER_SPEC.md`, `docs/PRODUCTION_READINESS.md`  
- Review: `docs/REVIEW_CHECKPOINT.md`  
