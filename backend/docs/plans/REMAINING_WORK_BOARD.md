# Remaining Work Board

**Date:** 2026-08-10  
**Main SHA (equality):** `5451a28` (local == `origin/main` after remaining-MVP wave)  
**Alembic head:** `q0d1e2f3a4b5`  
**Open PRs:** none for feature wave (docs close may be open briefly)  
**Branch protection:** `required_approving_review_count` = **1**  
**Production-ready?** **NO** — Phase 26 exit gate **NOT PASSED**

This board is the session handoff for next agents. Prefer small, mergeable slices.  
Do **not** claim production-ready. Do **not** spam multi-minute full pytest locally unless closing a PR.

---

## Snapshot

| Band | On main? | Depth | Next |
|------|----------|-------|------|
| 0–15.5 integrity | YES | Full for gate | Maintain only |
| 16 notifications/reports | YES | Console email + log MVP | Real SMTP/SMS/WA (P1/P2) |
| 17 API V1 | YES | 17A `/me/*` + auth login; 17B/C thin | Staff gaps + OpenAPI (P1) |
| 18 vertical E2E | YES | Service-layer PG **+ HTTP/ASGI** | Expand money path depth (P1) |
| 19 Admin Web | YES | Login + create member + create location | Cookie path, edit, day-1 ops (P1) |
| 20 Scanner PWA | YES | Camera QR + paste fallback | Device auth / offline (P1) |
| 21–24 hardening | YES | HSTS/CSP baseline + light RL | Deepen + LOCK (P1–P2) |
| 25 truth docs | YES | Docs | Keep in sync (P2) |
| 26 exit gate | Docs only | **FAIL** | Close criteria honestly |

**MVP surface ~80–85% · production polish ~15–20% open**

---

## P0 — next session (unblocks demos / truth)

| ID | Item | Owner hint | Notes / acceptance |
|----|------|------------|--------------------|
| P0-1 | **Demo seed usable** | DevEx | ✅ **CLOSED:** `backend/scripts/seed_demo.py` → `seed_demo_tenant.py` prints `bearer_token` + `tenant_id`; seeds GYM_OWNER + location + member. |
| P0-2 | **READY_TO_RUN exact URLs** | Docs | ✅ **CLOSED:** root `READY_TO_RUN.md` with ports 8000/5173/5174/5433 + seed + login. |
| P0-3 | **Admin login works end-to-end** | FE + BE | ✅ **CLOSED:** email/password via POST /api/v1/auth/login + Admin Login form; tenant_id from response. |
| P0-4 | **`fitness_app` role on long-lived volumes** | DevOps | Compose expects `fitness_app`; old volumes may only have `app_user`. Documented in READY_TO_RUN; consider one-shot bootstrap script or compose note. |
| P0-5 | **No open stale docs PRs** | Orchestrator | Keep open feature PR count at 0 after wave; close docs PR promptly. |
| P0-6 | **Docs SHA lag** | Docs | ✅ **CLOSED this wave:** PROGRESS / standing review / board bumped to `5451a28`. |

---

## P1 — product depth (toward Phase 26 PARTIAL → closer to PASS)

| ID | Item | Phase | Notes |
|----|------|-------|-------|
| P1-1 | Public **login API** (email/password → session cookie or token) | 17/19 | ✅ **CLOSED:** POST /api/v1/auth/login + logout; argon2 + hashed sessions + HttpOnly cookie. |
| P1-2 | Admin Web: create/edit member, create location | 19 | ✅ **CLOSED (create paths):** create member + create location forms. Still open: edit flows, membership/finance ops UI. |
| P1-3 | Admin Web: cookie/session path (HttpOnly) | 19/C4 | Align with `deps.get_session_token_from_cookie`; FE still stores token in localStorage for MVP. |
| P1-4 | Scanner: camera QR capture (not paste-only) | 20 | ✅ **CLOSED:** CameraQrScanner (BarcodeDetector / jsQR) + paste fallback. Device auth / offline still open. |
| P1-5 | HTTP/ASGI vertical e2e (member → QR → validate) | 18 | ✅ **CLOSED (baseline):** `backend/tests/e2e/test_http_vertical_slice.py` login/lists/QR via ASGI. Money-path depth still open. |
| P1-6 | Staff API gaps (17B) used by admin day-1 | 17 | Inventory OpenAPI vs UI needs. |
| P1-7 | OpenAPI completeness pass (17C) | 17 | Tags, examples, error models. |
| P1-8 | Notification adapters beyond log (email first) | 16/B10 | ✅ **partial CLOSED:** console email adapter (`NOTIFICATION_EMAIL_PROVIDER=console\|log`). Real SMTP deferred. |
| P1-9 | Report export real artifact (not placeholder metadata) | 16/B11 | Still MVP stub. |
| P1-10 | Phase 21: frontend build jobs as **required** checks | 21 | Branch protection currently: Security / Lint / Unit only. |
| P1-11 | Phase 23: HSTS + CSP + rate limit baseline | 23 | ✅ **CLOSED (baseline):** HSTS + API CSP in production env; TrustedHost if `ALLOWED_HOSTS`; nosniff/DENY/Referrer-Policy; login rate limit. Still not LOCKED / no CSRF / not multi-worker RL. |
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
| P2-6 | Real WhatsApp/SMS providers + webhook inbox | 16 | Keep Membership → Event → Notification path. Real email/SMTP too. |
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

1. **Admin cookie session:** stop localStorage token; rely on HttpOnly cookie from login.  
2. **Admin edit + day-1 ops:** member edit, membership freeze/renew surfaces, finance list.  
3. **Real email transport:** SMTP adapter behind same provider interface; env-gated.  
4. **Report export artifact:** non-placeholder file/bytes with tenant isolation tests.  
5. **Observability:** `/health` deps (db/redis) + basic metrics; no PII.  
6. **Branch protection FE builds:** require Admin Web + Scanner PWA build checks.

---

## Closed this orchestration session (remaining-MVP wave)

| Item | Evidence |
|------|----------|
| PR #38 admin create location | `frontend/admin-web/src/pages/Locations.tsx` form → POST `/api/v1/locations` |
| PR #39 HTTP/ASGI e2e | `backend/tests/e2e/test_http_vertical_slice.py` |
| PR #40 scanner camera QR | `frontend/scanner-pwa/src/components/CameraQrScanner.tsx` |
| PR #41 HSTS/CSP baseline | `backend/app/main.py` + `backend/tests/core/test_security_headers.py` |
| PR #42 console email adapter | `NOTIFICATION_EMAIL_PROVIDER` + `notification_providers.py` |
| Prior #37 auth login + create member | POST `/api/v1/auth/login`, Members create form |
| Inventory open feature PRs | `gh pr list --state open` → **0** (after wave) |
| Equality main | `5451a28` local == origin/main |
| Branch protection | review_count **1** restored after admin merges |
| Full pytest CI spam | **Not run** locally (CI only) |
| Phase 26 PASS claim | **Not claimed** — production-ready **NO** |

---

## References

- `docs/MASTER_SPEC.md`, `docs/PRODUCTION_READINESS.md`
- `docs/PROGRESS_CHECKLIST.md`, `docs/IMPLEMENTATION_MASTER_PLAN.md`
- `backend/docs/plans/phase26_core_mvp_exit_gate.md`
- `backend/docs/plans/MORNING_STATUS.md`
- `READY_TO_RUN.md`
