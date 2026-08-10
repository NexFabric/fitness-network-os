# Remaining Work Board

**Date:** 2026-08-10  
**Main SHA (equality):** `325d93d` (local == `origin/main` after UI brand + remaining-MVP)  
**Alembic head:** `q0d1e2f3a4b5`  
**Open PRs:** **0**  
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
| 19 Admin Web | YES | Login + create member/location + **brand** | Cookie path, edit, day-1 ops (P1) |
| 20 Scanner PWA | YES | Camera QR + paste + **Access brand** | Device auth / offline (P1) |
| 21–24 hardening | YES | HSTS/CSP baseline + light RL | Deepen + LOCK (P1–P2) |
| 25 truth docs | YES | Docs | Keep in sync (P2) |
| 26 exit gate | Docs only | **FAIL** | Close criteria honestly |

**MVP surface ~82–87% · production polish ~13–18% open**

---

## P0 — next session (unblocks demos / truth)

| ID | Item | Owner hint | Notes / acceptance |
|----|------|------------|--------------------|
| P0-1 | **Demo seed usable** | DevEx | ✅ **CLOSED:** `seed_demo.py` / `seed_demo_tenant.py` |
| P0-2 | **READY_TO_RUN exact URLs** | Docs | ✅ **CLOSED:** root `READY_TO_RUN.md` |
| P0-3 | **Admin login works end-to-end** | FE + BE | ✅ **CLOSED:** email/password login |
| P0-4 | **`fitness_app` role on long-lived volumes** | DevOps | Still open on old volumes; documented in READY_TO_RUN |
| P0-5 | **No open stale PRs** | Orchestrator | ✅ **CLOSED:** open count **0** after #44/#45 |
| P0-6 | **Docs SHA lag** | Docs | ✅ **CLOSED this pass:** bump to `325d93d` |

---

## P1 — product depth (toward Phase 26 PARTIAL → closer to PASS)

| ID | Item | Phase | Notes |
|----|------|-------|-------|
| P1-1 | Public **login API** | 17/19 | ✅ **CLOSED** |
| P1-2 | Admin Web: create member/location | 19 | ✅ **CLOSED (create)**; edit still open |
| P1-2b | Admin Web **brand system** | 19 | ✅ **CLOSED:** #45 + `frontend/UI_BRAND_SYSTEM.md` |
| P1-3 | Admin Web: cookie/session path (HttpOnly) | 19/C4 | FE still localStorage token MVP |
| P1-4 | Scanner camera QR | 20 | ✅ **CLOSED** (#40) |
| P1-4b | Scanner Access brand polish | 20 | ✅ **CLOSED** (#44) |
| P1-5 | HTTP/ASGI vertical e2e | 18 | ✅ **CLOSED (baseline)** (#39) |
| P1-6 | Staff API gaps (17B) used by admin day-1 | 17 | Open |
| P1-7 | OpenAPI completeness pass (17C) | 17 | Open |
| P1-8 | Notification adapters beyond log | 16/B10 | ✅ **partial:** console email; real SMTP open |
| P1-9 | Report export real artifact | 16/B11 | Open |
| P1-10 | FE builds as **required** checks | 21 | Protection still Security/Lint/Unit only |
| P1-11 | HSTS + CSP + rate limit baseline | 23 | ✅ **CLOSED (baseline)** (#41); not LOCKED |
| P1-12 | Health/deps + metrics | 24 | Open |

---

## P2 — production bar / LOCK hygiene

| ID | Item | Phase | Notes |
|----|------|-------|-------|
| P2-1 | `Dockerfile.prod` digest pins, HEALTHCHECK, SBOM | 22 | Sketch exists |
| P2-2 | Prod compose / secrets injection | 22/C12 | Open |
| P2-3 | Privileged MFA enforcement | C5 | Foundation only |
| P2-4 | Formal threat models | C9 | Open |
| P2-5 | CONTRACT DROP legacy floats | 11/C10 | Deferred |
| P2-6 | Real WhatsApp/SMS + webhook inbox | 16 | Open |
| P2-7 | Backup/restore drill evidence | 26 | Exit gate |
| P2-8 | ASVS / pentest + independent APPROVE | 26/D5 | Exit gate |
| P2-9 | Phase 16–24 **LOCKED** after depth CI | 25 | MVP ≠ LOCKED |
| P2-10 | Require Admin + Scanner build checks | 21 | Optional |

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

1. **Admin cookie session** — stop localStorage token; rely on HttpOnly cookie.  
2. **Admin day-1 ops** — member edit, membership freeze/renew, finance lists.  
3. **Real email SMTP** — env-gated behind NotificationProvider.  
4. **Report export artifact** — non-placeholder bytes + tenancy tests.  
5. **Observability** — `/health` deps + metrics; no PII.  
6. **Branch protection** — require Admin Web + Scanner PWA builds.

---

## Closed this session (UI brand + docs truth)

| Item | Evidence |
|------|----------|
| PR #44 Scanner brand | GymClubNex · Access, GRANT/DENY UX |
| PR #45 Admin brand | Teal brand tokens, login/shell/dashboard |
| UI brand contract | `frontend/UI_BRAND_SYSTEM.md` |
| Prior remaining-MVP #37–#42 | Auth, CRUD create, camera, e2e, HSTS, console email |
| Docs SHA | `325d93d` |
| Open PRs | **0** |
| Branch protection | review_count **1** |
| Phase 26 PASS | **Not claimed** |

---

## References

- `docs/MASTER_SPEC.md`, `docs/PRODUCTION_READINESS.md`
- `docs/PROGRESS_CHECKLIST.md`, `docs/IMPLEMENTATION_MASTER_PLAN.md`
- `backend/docs/plans/phase26_core_mvp_exit_gate.md`
- `backend/docs/plans/MORNING_STATUS.md`
- `frontend/UI_BRAND_SYSTEM.md`
- `READY_TO_RUN.md`
