# Standing Review — morning (remaining readiness)

**Date:** 2026-08-10  
**Reviewer mode:** light (no long pytest)  
**Main HEAD:** `e19d935` (local == product stack after PR #26 + docs #28/#30/#32)  
**Alembic head:** `q0d1e2f3a4b5` (Phase 16; after 15.5 `p9c0d1e2f3a4`)

## Verdict: **HEALTHY_MVP**

| Signal | Result |
|--------|--------|
| Runnable? | **YES** |
| Production-ready? | **NO** |
| Phase 26 exit gate | **FAIL / NOT PASSED** |
| Overall vs Phase 0–26 | **~75–80% MVP on main** · **~20–25% prod bar open** |

**Do not claim production-ready.**

## Session update (orchestrator — remaining MVP slice)

**Branch:** `feat/complete-remaining-mvp` (not main until merged)  
**Delta:** public auth login/logout, seed_demo path, Admin password login + create member form, light login rate limit.  
**Production-ready?** **NO** — Phase 26 still **NOT PASSED**.  
**Branch protection:** restore `review_count=1` after any emergency merge.


---

## 1. App runnable (live check)

| Check | Result |
|-------|--------|
| `docker compose` postgres | Up, healthy (`:5433→5432`) |
| `docker compose` redis | Up, healthy (`:6379`) |
| `docker compose` backend | Up (`:8000`) |
| `GET http://localhost:8000/health` | **200** `{"status":"ok",...}` |
| `GET http://localhost:8000/docs` | **200** |
| Admin Web `http://localhost:5173/` | **200** (Vite dev) |
| Scanner PWA `http://localhost:5174/` | **200** (Vite dev) |
| FE dist artifacts | present under `frontend/*/dist/` |

**Compose note:** FE are host Vite processes, not compose services (matches `READY_TO_RUN.md`). Backend may be compose or host; health is green either way.

---

## 2. Completeness vs MVP

| Band | On main | Depth |
|------|---------|--------|
| 0–15.5 domain + integrity | YES (`125a8c6` lineage) | Full for integrity track |
| 16–20 product MVP | YES (PR #26 → `5046f10`) | **MVP / PARTIAL depth** |
| 21–24 hardening | YES (same stack) | Light MVP / stubs |
| 25 checklist truth | YES (docs) | Process only |
| 26 exit gate | Scorecard on main | **FAIL** |

**MVP:** shippable for local demo / internal dev (API + minimal admin + paste-QR scanner + core domain).  
**Not complete product:** real transports, day-1 ops UI, full HTTP E2E, production security/ops bar.

---

## 3. Docs vs main after PR #26

| Claim | Truth |
|-------|--------|
| PR #26 on main | **YES** — ancestor of `e19d935` |
| Alembic on main includes Phase 16 `q0…` | **YES** |
| “16–20 not merged” | **STALE if present** — ignore |
| Checklist / master plan / REVIEW_CHECKPOINT HEAD `398e858` | **SHA lag** (actual tip `e19d935`; product truth still correct) |
| `AGENTS.md` “Active = Phase 16–20 on PR #26” + alembic `p9…` only | **STALE wording** — stack merged; head is `q0…`; exit still open |
| Phase 26 production-ready | **NO** everywhere that matters |

Docs are **mostly consistent on product truth** (merged MVP, not prod). Residual: SHA / “active PR” wording drift — cosmetic, not code risk.

---

## Remaining backlog (top 10)

1. **Real notification providers** (email/SMS/WhatsApp) behind adapters — log-only today  
2. **Admin Web depth** — password login + create member landed on branch; still need edit, locations create, finance/membership ops  
3. **Scanner PWA depth** — camera scan, offline/gateway story, device auth (beyond paste → validate)  
4. **Phase 17B/C** — staff API gaps + OpenAPI completeness for day-1 admin  
5. **HTTP/ASGI vertical E2E** (access + money path); service-layer e2e alone is not product E2E  
6. **HTTP security baseline** — HSTS, CSP, CSRF posture, TrustedHost, rate limit, prod CORS discipline  
7. **Observability productization** — health/deps checks, metrics/traces, alerts (beyond request-id access log)  
8. **Container / supply chain** — prod compose profile, HEALTHCHECK, digest pins, SBOM/signing path  
9. **Ops readiness** — backup/restore drill, secrets runtime isolation, ASVS/pentest evidence  
10. **Phase 26 re-score + independent APPROVE** — only then any production-ready claim  

---

## Explicit non-claims

- Not **production-ready**  
- Not **PRODUCTION VERIFIED**  
- Not Phase 26 **PASS**  
- MERGED MVP ≠ production bar  

## Morning path

1. Work from **main** (`e19d935`+); pull first.  
2. Prefer backlog items that close Phase 26 **PARTIAL → PASS** themes (providers, FE depth, HTTP E2E, security/ops).  
3. Optional: bump stale Main HEAD strings in checklist / AGENTS / REVIEW_CHECKPOINT (docs-only).  
4. Re-score `phase26_core_mvp_exit_gate.md` only with evidence — never self-declare prod.

## Control path

Continue hardening PARTIALS; keep standing review honest; never claim production-ready until Phase 26 required criteria all PASS.
