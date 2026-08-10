# Standing Review — remaining-MVP wave close

**Date:** 2026-08-10  
**Reviewer mode:** light (no long pytest)  
**Main HEAD:** `5451a28` (local == `origin/main` after PRs #37–#42)  
**Alembic head:** `q0d1e2f3a4b5` (Phase 16; after 15.5 `p9c0d1e2f3a4`)

## Verdict: **HEALTHY_MVP**

| Signal | Result |
|--------|--------|
| Runnable? | **YES** |
| Production-ready? | **NO** |
| Phase 26 exit gate | **FAIL / NOT PASSED** |
| Overall vs Phase 0–26 | **~80–85% MVP on main** · **~15–20% prod bar open** |

**Do not claim production-ready.**

## Session update (orchestrator — remaining-MVP wave)

**Merged on main (this wave):**

| PR | Slice |
|----|--------|
| #37 | Auth login + seed password path + admin create member |
| #38 | Admin create location form |
| #39 | HTTP/ASGI vertical e2e |
| #40 | Scanner camera QR (paste fallback kept) |
| #41 | HSTS + CSP baseline (+ optional TrustedHost) |
| #42 | Console email adapter (`NOTIFICATION_EMAIL_PROVIDER`) |

**Production-ready?** **NO** — Phase 26 still **NOT PASSED**.  
**Branch protection:** `required_approving_review_count` **1** (restored after temporary emergency merges).

---

## 1. App runnable (live check)

| Check | Result |
|-------|--------|
| `docker compose` postgres | Up, healthy (`:5433→5432`) |
| `docker compose` redis | Up, healthy (`:6379`) |
| `docker compose` backend | Up (`:8000`) |
| `GET http://localhost:8000/health` | **200** `{"status":"ok",...}` |
| OpenAPI `/api/v1/auth/login` | **present** (POST) |
| OpenAPI `/api/v1/locations` | **present** (GET/POST) |
| Admin Web `http://localhost:5173/` | **200** (Vite dev) |
| Scanner PWA `http://localhost:5174/` | **200** (Vite dev) |

**Compose note:** FE are host Vite processes, not compose services (matches `READY_TO_RUN.md`).

---

## 2. Completeness vs MVP

| Band | On main | Depth |
|------|---------|--------|
| 0–15.5 domain + integrity | YES (`125a8c6` lineage) | Full for integrity track |
| 16–20 product MVP | YES (PR #26 + #37–#42) | **MVP + remaining-wave depth** |
| 21–24 hardening | YES | Baseline headers + light RL (not LOCKED) |
| 25 checklist truth | YES (docs) | Process only |
| 26 exit gate | Scorecard on main | **FAIL** |

**MVP:** local demo / internal dev (API + admin login/CRUD basics + camera QR scanner + console email + HTTP e2e).  
**Not complete product:** real transports, day-1 ops UI polish, production security/ops bar, independent APPROVE.

---

## 3. Docs vs main

| Claim | Truth |
|-------|--------|
| Remaining-MVP feature PRs #37–#42 | **MERGED** on `5451a28` |
| Alembic head | **`q0d1e2f3a4b5`** |
| Phase 26 production-ready | **NO** |
| Board / PROGRESS SHA lag | Bumped in this docs close |

---

## Remaining backlog (top 10)

1. **Real notification transports** — SMTP/SMS/WhatsApp; console email is not production  
2. **Admin cookie-only session** — drop localStorage token path  
3. **Admin day-1 ops depth** — edit member, membership lifecycle UI, finance surfaces  
4. **Scanner device auth / offline** — beyond camera + paste validate  
5. **Phase 17B/C** — staff API gaps + OpenAPI completeness  
6. **HTTP E2E money path** — access path covered; finance slice still thin  
7. **Hardening LOCK** — CSRF, multi-worker rate limit, required FE CI checks  
8. **Observability** — health/deps, metrics/traces, alerts  
9. **Container / supply chain** — prod compose, HEALTHCHECK, digests, SBOM  
10. **Phase 26 re-score + independent APPROVE** — only then any production-ready claim  

---

## Explicit non-claims

- Not **production-ready**  
- Not **PRODUCTION VERIFIED**  
- Not Phase 26 **PASS**  
- MERGED MVP ≠ production bar  

## Control path

Keep standing review honest; never claim production-ready until Phase 26 required criteria all PASS with independent human APPROVE.
