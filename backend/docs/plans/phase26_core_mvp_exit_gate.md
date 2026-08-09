# Phase 26 — CORE MVP EXIT GATE

**Status:** 🔴 **OPEN — overall FAIL for production-ready**  
**Date:** 2026-08-10  
**Scored against:** main `5046f10` (PR #26 merge; includes 15.5 `125a8c6` lineage)  
**Truth model:** `backend/docs/plans/phase25_checklist_truth.md`  
**Do not claim production-ready** until this gate is **PASS**.

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

### A2. Product stack 16–20 (on main via PR #26 merge `5046f10`)

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| A2.1 | Phase 16 notifications/reports services + API | **PARTIAL** | **IMPLEMENTED on main** (`q0d1e2f3a4b5`, services, RBAC, tests). Log provider only; no real transports. |
| A2.2 | Phase 17 API V1 completion | **PARTIAL** | **17A** `/me/*` on main. **17B** staff gaps / **17C** OpenAPI **not done**. |
| A2.3 | Phase 18 vertical slice E2E | **PARTIAL** | Service-layer PG e2e on main. **HTTP/ASGI E2E deferred.** No finance vertical. |
| A2.4 | Phase 19 Admin Web MVP | **PARTIAL** | Scaffold on main: token paste, members/locations. No cookie auth / create-edit / finance UI. |
| A2.5 | Phase 20 Scanner PWA MVP | **PARTIAL** | Scaffold on main: paste QR. No camera, offline gateway, device auth. |
| A2.6 | Stack 16–20 merged to main + required CI green | **PARTIAL** | Merged PR #26 → `5046f10`. Post-merge main CI must stay green (FE builds already green on merge run). |

**Band A2 summary:** **PARTIAL** (shipped MVP on main; product depth incomplete).

---

### A3. Hardening track 21–25

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| A3.1 | Phase 21 CI V2 includes frontend builds | **PARTIAL** | Jobs on main CI; green on merge/PR. Not all FE jobs are **required** branch-protection checks. |
| A3.2 | Phase 22 production containers | **PARTIAL** | `Dockerfile.prod` multi-stage non-root; no SBOM/signing/HEALTHCHECK/prod compose. |
| A3.3 | Phase 23 HTTP security baseline | **PARTIAL** | Prod CORS + nosniff/DENY; no HSTS/CSP/CSRF/TrustedHost. |
| A3.4 | Phase 24 observability | **PARTIAL** | RequestLoggingMiddleware on main; no OTel/metrics. |
| A3.5 | Phase 25 checklist truth model | **PARTIAL** | Truth model docs on main; no automated enforcement. |

**Band A3 summary:** **PARTIAL** (MVP hardening on main; not production-complete).

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
| B10 | Notifications path Domain → Event → Outbox → Adapter | **PARTIAL** | Phase 16 on main; log adapter only; no provider webhooks |
| B11 | Reports definitions/runs | **PARTIAL** | Phase 16 on main; placeholder export metadata |
| B12 | MEMBER self-service without BOLA | **PARTIAL** | 15.5 + 17A `/me/*` on main; full surface incomplete |
| B13 | Executable vertical access slice | **PARTIAL** | Service e2e on main; not full product E2E |
| B14 | Staff admin UI usable for day-1 ops | **PARTIAL** | Minimal admin-web scaffold |
| B15 | Door scanner path usable | **PARTIAL** | Minimal scanner-pwa scaffold |

---

## C. Security & production-readiness exit criteria

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| C1 | No raw PAN/CVV storage/logging | **PASS** | Policy + architecture (card data out of scope) |
| C2 | No Membership → WhatsApp shortcut | **PASS** | Bridge/outbox pattern; architecture fitness tests on branch |
| C3 | Public generic outbox/inbox not reintroduced | **PASS** | Main + stack (notifications/reports only) |
| C4 | Session/auth production posture (HttpOnly cookie browser path, timeouts) | **PARTIAL** | Server sessions exist; browser apps still paste Bearer tokens |
| C5 | Privileged MFA enforced for owner/admin roles | **PARTIAL** | MFA foundation IMPLEMENTED; not full production enforcement claim |
| C6 | ASVS / web baseline (HSTS, CSP, CSRF, CORS allowlist) | **PARTIAL** | CORS allowlist + two headers only |
| C7 | Container non-root prod image path | **PARTIAL** | `Dockerfile.prod` sketch; not full supply-chain |
| C8 | Observability without PII cardinality blow-ups | **PARTIAL** | Phase 24 stub: request/correlation ids + structured access log (no body/query/auth). Full OTel/metrics still open. |
| C9 | Threat models + business invariant coverage for hot domains | **PARTIAL** | Many domain tests; formal threat models incomplete |
| C10 | Zero-downtime migration discipline (expand/contract) | **PARTIAL** | Expand used (e.g. Phase 11); CONTRACT DROP deferred by design |
| C11 | Supply chain (SAST/SCA/secrets in CI) | **PARTIAL** | Bandit, pip-audit, TruffleHog, Safety present; SBOM/license scan incomplete |
| C12 | Production secrets isolation & no secrets in images | **PARTIAL** | Images avoid baking `.env`; full runtime story incomplete |

---

## D. Process / merge gate criteria

| # | Criterion | Score | Evidence / gap |
|---|-----------|-------|----------------|
| D1 | Phase 15.5 on main with CI VERIFIED docs | **PASS** | `125a8c6` + progress docs |
| D2 | Phase 16–20 MERGED to main | **PASS** | PR #26 merge `5046f10` |
| D3 | Required CI green on main after stack merge | **PARTIAL** | Merge-time PR CI green; post-merge main workflow must stay green |
| D4 | Checklist + master plan match git reality | **PARTIAL** | Post-merge truth sync (this docs pass) |
| D5 | Independent human APPROVE for production claim | **FAIL** | Exit gate not open for claim |
| D6 | Explicit deferred list published (not silent) | **PASS** | Checklist “Known intentional deferrals” + phase plans |

---

## E. Overall gate decision

| Aggregate | Result |
|-----------|--------|
| Band A (0–15.5 on main) | **PASS** |
| Band A2 (16–20) | **PARTIAL** (on main, depth incomplete) |
| Band A3 (21–25) | **PARTIAL** |
| Functional B | **PARTIAL** (core domain PASS; ops surfaces PARTIAL) |
| Security C | **PARTIAL** |
| Process D | **PARTIAL** (merged; no prod APPROVE) |
| **CORE MVP EXIT GATE** | 🔴 **FAIL** |
| **Production-ready?** | **NO** |

### Why FAIL (blocking themes)

1. **Product depth incomplete** — log-only notifications, service-layer E2E (not HTTP), admin/scanner scaffolds only.  
2. **Hardening incomplete** — light CORS/headers/container/obs; FE CI jobs not all required checks; no backup/restore drill.  
3. **Operator UX incomplete** — not day-1 production ops.  
4. **No formal production APPROVE** — gate intentionally closed.

### What would move the gate toward PASS (ordered)

1. Confirm post-merge main CI stays green; keep docs honest (IMPLEMENTED on main ≠ production-ready).  
2. Close 17B/17C critical staff/OpenAPI gaps needed by admin.  
3. At least one HTTP vertical E2E (or product sign-off for service-only risk).  
4. Make Phase 21 FE builds required checks if desired; deepen 22–23 baseline.  
5. Deepen Phase 24 (health/deps, error rates, optional OTel); document backup/restore.  
6. Re-score this document; independent APPROVE; only then claim production-ready.

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
