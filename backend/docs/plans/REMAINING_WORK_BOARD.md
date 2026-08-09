# Remaining Work Board

**Date:** 2026-08-10  
**Main SHA (equality):** `e19d935` (local == `origin/main` at board authoring)  
**Alembic head:** `q0d1e2f3a4b5`  
**Open PRs:** **none**  
**Branch protection:** `required_approving_review_count` = **1**  
**Production-ready?** **NO** — Phase 26 exit gate **NOT PASSED**

This board is the session handoff for next agents. Prefer small, mergeable slices.  
Do **not** claim production-ready. Do **not** spam multi-minute full pytest locally unless closing a PR.

---

## Snapshot

| Band | On main? | Depth | Next |
|------|----------|-------|------|
| 0–15.5 integrity | YES | Full for gate | Maintain only |
| 16 notifications/reports | YES | Log adapter MVP | Real transports (P1) |
| 17 API V1 | YES | 17A `/me/*`; 17B/C thin | Staff gaps + OpenAPI (P1) |
| 18 vertical E2E | YES | Service-layer PG | HTTP/ASGI e2e (P1) |
| 19 Admin Web | YES | Token paste + lists | Cookie login, CRUD (P0 UX) |
| 20 Scanner PWA | YES | Paste validate | Camera / device auth (P1) |
| 21–24 hardening | YES | Light MVP | Deepen + LOCK (P1–P2) |
| 25 truth docs | YES | Docs | Keep in sync (P2) |
| 26 exit gate | Docs only | **FAIL** | Close criteria honestly |

**MVP surface ~75–80% · production polish ~20–25% open**

---

## P0 — next session (unblocks demos / truth)

| ID | Item | Owner hint | Notes / acceptance |
|----|------|------------|--------------------|
| P0-1 | **Demo seed usable** | DevEx | ✅ **CLOSED this session:** `backend/scripts/seed_demo.py` → `seed_demo_tenant.py` prints `bearer_token` + `tenant_id`; seeds GYM_OWNER + location + member. |
| P0-2 | **READY_TO_RUN exact URLs** | Docs | ✅ **CLOSED this session:** root `READY_TO_RUN.md` with ports 8000/5173/5174/5433 + seed steps. |
| P0-3 | **Admin login works end-to-end** | FE + BE | After seed: open http://localhost:5173/login → paste token + tenant → Members/Locations non-empty. Manual verify remaining if FE not started. |
| P0-4 | **`fitness_app` role on long-lived volumes** | DevOps | Compose expects `fitness_app`; old volumes may only have `app_user`. Documented in READY_TO_RUN; consider one-shot bootstrap script or compose note. |
| P0-5 | **No open stale docs PRs** | Orchestrator | ✅ **CLOSED:** open PR count **0** (#31/#33 closed, #32 merged). |
| P0-6 | **Docs SHA lag** | Docs | `PROGRESS_CHECKLIST` / master plan may still mention older SHAs (`398e858` / `4120b7f`). Bump to current main when editing those files. |

---

## P1 — product depth (toward Phase 26 PARTIAL → closer to PASS)

| ID | Item | Phase | Notes |
|----|------|-------|-------|
| P1-1 | Public **login API** (email/password → session cookie or token) | 17/19 | Removes token-paste UX; keep argon2 + hashed sessions. |
| P1-2 | Admin Web: create/edit member, create location | 19 | Today list-only. |
| P1-3 | Admin Web: cookie/session path (HttpOnly) | 19/C4 | Align with `deps.get_session_token_from_cookie`. |
| P1-4 | Scanner: camera QR capture (not paste-only) | 20 | Keep offline/device auth deferred if needed. |
| P1-5 | HTTP/ASGI vertical e2e (member → QR → validate) | 18 | Service e2e exists; ASGI missing. |
| P1-6 | Staff API gaps (17B) used by admin day-1 | 17 | Inventory OpenAPI vs UI needs. |
| P1-7 | OpenAPI completeness pass (17C) | 17 | Tags, examples, error models. |
| P1-8 | Notification adapters beyond log (email first) | 16/B10 | Domain → Event → Outbox → Adapter only. |
| P1-9 | Report export real artifact (not placeholder metadata) | 16/B11 | Still MVP stub. |
| P1-10 | Phase 21: frontend build jobs as **required** checks | 21 | Branch protection currently: Security / Lint / Unit only. |
| P1-11 | Phase 23: HSTS + CSP + rate limit baseline | 23 | CORS allowlist already env-gated. |
| P1-12 | Phase 24: health/deps + metrics beyond request-id stub | 24 | No PII in logs. |

---

## P2 — production bar / LOCK hygiene

| ID | Item | Phase | Notes |
|----|------|-------|-------|
| P2-1 | `Dockerfile.prod` digest pins, HEALTHCHECK, SBOM | 22 | Multi-stage non-root sketch exists. |
| P2-2 | Prod compose profile / secrets injection story | 22/C12 | No secrets in images. |
| P2-3 | Privileged MFA enforcement claim for owner/admin | C5 | Foundation only. |
| P2-4 | Formal threat models for membership/finance/access | C9 | Tests ≠ threat models. |
| P2-5 | Expand/contract: schedule CONTRACT DROP of legacy floats | 11/C10 | Intentional deferral. |
| P2-6 | Real WhatsApp/SMS providers + webhook inbox | 16 | Keep Membership → Event → Notification path. |
| P2-7 | Backup/restore runbook + drill evidence | 26 | Exit gate. |
| P2-8 | ASVS / pentest evidence + independent APPROVE | 26/D5 | Required for production-ready claim. |
| P2-9 | Phase 16–24 **LOCKED** docs after depth CI VERIFIED | 25 | MVP MERGED ≠ LOCKED. |
| P2-10 | Branch protection: add Admin Web + Scanner build required | 21 | Optional until FE is critical path. |

---

## Explicit non-work / do-not

- Do **not** reintroduce public generic outbox/inbox inject.
- Do **not** store PAN/CVV or log card data.
- Do **not** use float for money (`amount_minor` only).
- Do **not** shortcut Membership → WhatsApp.
- Do **not** add Kafka/K8s/microservices without ADR.
- Do **not** set `review_count=0` permanently — restore **1** after emergency merges.
- Do **not** claim Phase 26 PASS without independent human APPROVE.

---

## Suggested agent slices (next sessions)

1. **Auth slice:** `POST /api/v1/auth/login` + set HttpOnly cookie; Admin Login form email/password.  
2. **Admin CRUD slice:** member create form + location create form against existing APIs.  
3. **Scanner camera slice:** getUserMedia + jsQR (or similar) → existing validate endpoint.  
4. **HTTP e2e slice:** pytest + httpx ASGI transport reusing seed patterns.  
5. **Email adapter slice:** Outbox consumer + console/SMTP provider behind interface.  
6. **Hardening slice:** TrustedHost + rate limit middleware + CSP header (env-flagged).

---

## Closed this orchestration session

| Item | Evidence |
|------|----------|
| Inventory open PRs | `gh pr list --state open` → **0** |
| Equality main | `e19d935` local == origin/main |
| Demo seed | `scripts/seed_demo.py` / `seed_demo_tenant.py`; verified `/api/v1/members` + `/locations` 200 |
| READY_TO_RUN polish | Root `READY_TO_RUN.md` |
| Remaining board | This file |
| Branch protection | review_count **1** (no change needed) |
| Full pytest CI spam | **Not run** (per constraints) |

---

## References

- `docs/MASTER_SPEC.md`, `docs/PRODUCTION_READINESS.md`
- `docs/PROGRESS_CHECKLIST.md`, `docs/IMPLEMENTATION_MASTER_PLAN.md`
- `backend/docs/plans/phase26_core_mvp_exit_gate.md`
- `backend/docs/plans/MORNING_STATUS.md`
- `READY_TO_RUN.md`
