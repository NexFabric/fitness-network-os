# Standing Review — post UI brand + remaining-MVP

**Date:** 2026-08-10  
**Reviewer mode:** light (no long pytest)  
**Main HEAD:** `325d93d` (local == `origin/main`)  
**Alembic head:** `q0d1e2f3a4b5` (Phase 16; after 15.5 `p9c0d1e2f3a4`)

## Verdict: **HEALTHY_MVP**

| Signal | Result |
|--------|--------|
| Runnable? | **YES** |
| Production-ready? | **NO** |
| Phase 26 exit gate | **FAIL / NOT PASSED** |
| Overall vs Phase 0–26 | **~82–87% MVP on main** · **~13–18% prod bar open** |

**Do not claim production-ready.**

## Merged on main (cumulative waves)

| PR | Slice |
|----|--------|
| #25 | Phase 15.5 integrity |
| #26 | Phases 16–26 stack MVP |
| #37 | Auth login + seed password + admin create member |
| #38 | Admin create location |
| #39 | HTTP/ASGI vertical e2e |
| #40 | Scanner camera QR |
| #41 | HSTS + CSP baseline |
| #42 | Console email adapter |
| #43 | Docs remaining-MVP close |
| #44 | Scanner UI brand (Access) |
| #45 | Admin UI brand system |

**Branch protection:** `required_approving_review_count` **1**  
**Open PRs:** **0**

---

## 1. App runnable (live check pattern)

| Check | Result |
|-------|--------|
| Postgres `:5433` / Redis `:6379` | Docker healthy |
| Backend `:8000` `/health` | **200** |
| OpenAPI auth login | present |
| Admin Web `:5173` | Vite; branded staff console |
| Scanner PWA `:5174` | Vite; GymClubNex · Access |

**Demo login:** `demo.admin@demo.local` / `DemoAdmin123!` after `uv run python scripts/seed_demo.py`

---

## 2. Completeness vs MVP

| Band | On main | Depth |
|------|---------|--------|
| 0–15.5 | YES | Integrity track complete for gate |
| 16–20 | YES | Product MVP + brand + camera + auth |
| 21–24 | YES | Baseline headers/RL (not LOCKED) |
| 25–26 | Docs | Exit **FAIL** |

**MVP:** local/internal demo (login, member/location create, scanner camera/paste, console email, HTTP e2e, branded UI).  
**Not complete product:** real transports, cookie-only session, full day-1 ops UI, production ops bar, independent APPROVE.

---

## 3. Docs vs main

| Claim | Truth |
|-------|--------|
| Feature PRs #37–#45 | **MERGED** on `325d93d` |
| Alembic head | **`q0d1e2f3a4b5`** |
| Phase 26 production-ready | **NO** |
| Checklist / board SHA | Aligned this pass |

---

## Remaining backlog (top 10)

1. Real notification transports (SMTP/SMS/WhatsApp)  
2. Admin cookie-only session  
3. Admin day-1 ops (edit, membership lifecycle, finance UI)  
4. Scanner device auth / offline  
5. Phase 17B/C staff API + OpenAPI  
6. HTTP E2E money path depth  
7. Hardening LOCK (CSRF, multi-worker RL, required FE CI checks)  
8. Observability (health deps, metrics, alerts)  
9. Container / supply chain (prod compose, SBOM, digests)  
10. Phase 26 re-score + independent APPROVE  

---

## Explicit non-claims

- Not **production-ready**  
- Not **PRODUCTION VERIFIED**  
- Not Phase 26 **PASS**  
- MERGED MVP ≠ production bar  
