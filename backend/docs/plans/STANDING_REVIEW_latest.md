# Standing Review — Phase 16–20 stack (branch)

**Date:** 2026-08-10  
**Branch:** `feat/phase16-notifications-reports`  
**Reviewer role:** integrator / standing review (automated orchestrator pass)  
**Verdict:** 🟠 **CLEAN enough to continue** on branch — **not LOCKED** · **not production-ready**

---

## Scope reviewed

| Band | Status on branch | Notes |
|------|------------------|-------|
| Phase 15.5 integrity (base) | PR #25 CI green | **not LOCKED** — human APPROVE + merge still open |
| Phase 15.6 residual | DONE on stack | ops CLI + dedupe 200/201 |
| Phase 16 Notifications/Reports | IMPLEMENTED + integrity CLEAN | PR #26 stacked; merge **after** 15.5 only |
| Phase 17A `/me/*` | **IMPLEMENTED on branch** | profile/member/memberships/entitlements/checkins |
| Phase 18 vertical slice E2E | **IMPLEMENTED on branch** | service-layer PG slice; HTTP E2E deferred |
| Phase 19 Admin Web MVP | **IMPLEMENTED on branch** | multi-page scaffold + API lists |
| Phase 20 Scanner PWA MVP | **IMPLEMENTED on branch** | validate QR UI + shell SW |

**Commits (logical stack tip):**

| SHA | Subject |
|-----|---------|
| `7daef72` | feat(phase19-20): admin-web + scanner-pwa MVP scaffolds |
| `d6e24ed` | feat(phase18): vertical slice e2e |
| `8511670` | feat(phase17): me self-service expansion |
| `b272315` | feat(phase16-17): residual P2 / bridge / ops CLI / phase17 plan |

---

## Hard rules checklist

| Rule | Verdict | Evidence |
|------|---------|----------|
| Gym = Tenant; Branch = Location | **PASS** | Admin Locations page; models/API |
| User ≠ Member | **PASS** | `/me/*` bind via `members.user_id`; staff list separate |
| `require_self` for MEMBER `/me/*` | **PASS** | `me.py` — no client `member_id` |
| No public outbox/inbox inject | **PASS** | Phase 15.5C still holds; CLI is ops-only |
| No float money | **PASS** | No new money fields in 17–20 |
| Domain → Outbox → Adapter | **PASS** | NotificationBridge; Membership does not import providers |
| MEMBER BOLA closed | **PASS** | Tests: staff path 403; self bind only; wrong tenant 403 |

---

## Phase 16 residual (close)

| Item | Verdict |
|------|---------|
| IR P2 reliability (report FAILED, handler DEAD, free-form) | **CLOSED on branch** |
| `process_notification_due` CLI | **CLOSED** (ops; not public HTTP) |
| NotificationBridge | **Helper only** — not wired into MembershipService |
| Integrity closeout doc | **CLEAN** |
| LOCKED | **NO** |

Focused suite earlier: 37+ notification/report/bridge/API tests green on isolated PG `:5433`.

---

## Phase 17A — `/me/*`

| Route | Authz | Status |
|-------|-------|--------|
| `GET /me/profile` | `profile:read` + owner | Landed |
| `GET /me/member` | `memberships:read:self` | Landed |
| `GET /me/memberships` | `memberships:read:self` | Landed |
| `GET /me/entitlements` | `entitlements:read:self` | Landed |
| `GET /me/checkins` | `checkins:read:self` | Landed (read list only) |
| `POST /me/entitlements/check` | `entitlements:check:self` | Pre-existing + regression |

**Tests:** `tests/api/test_me_self_service.py` — allow / unbound 404 / wrong-tenant 403 / BOLA / staff list OK.  
**Verified:** 8 me tests + trust-boundary suite green with e2e (15 passed combined slice).

**Gaps:** 17B staff router completeness, 17C OpenAPI polish; `profile:read` still not `profile:read:self` (documented careful path).

---

## Phase 18 — Vertical slice

| Case | Layer | Status |
|------|-------|--------|
| org → member bind → issue → validate GRANT | Service + real PG | **PASS** |
| staff issue + malformed deny | Service | **PASS** |
| NotificationBridge optional | Service | **PASS** |
| Full HTTP ASGI E2E | Deferred | Gap |
| Payment → membership activate | Deferred | Gap |
| app_user RLS runtime | Separate tenancy tests | Gap for this slice |

**Paths:** `tests/e2e/test_vertical_slice_access.py`, alias `test_vertical_slice_member_qr.py`.

---

## Phase 19–20 — Frontends

| App | Build | Notes |
|-----|-------|-------|
| `frontend/admin-web` | `tsc && vite build` **green** | Login shell, members, locations |
| `frontend/scanner-pwa` | `tsc && vite build` **green** | Validate QR, manifest + SW |

**Gaps:** camera scan, real cookie login API, frontend CI, production TLS/headers (Phase 22–23).

---

## Test results (this review pass)

| Suite | Result |
|-------|--------|
| Phase 16 residual focused (prior) | 37 passed |
| `test_me_self_service` + 15.5c + e2e | **15 passed** (~39s, PG `:5433`) |
| admin-web build | **OK** |
| scanner-pwa build | **OK** |

---

## Remaining to Phase 26 (honest)

| Phase | Remaining work |
|-------|----------------|
| 15.5 | Independent APPROVE → merge → main CI → LOCKED |
| 16 | Rebase/merge after 15.5; PR CI green → LOCKED |
| 17 | 17B staff gaps, 17C OpenAPI; merge after 16 preferred |
| 18 | Optional HTTP E2E; finance vertical; RLS runtime path |
| 19–20 | Real auth login, richer CRUD, camera, frontend CI |
| 21 | CI V2 full verification (include frontends) |
| 22 | Production container hardening |
| 23 | HTTP security baseline |
| 24 | Observability |
| 25 | Checklist truth model automation |
| 26 | CORE MVP EXIT GATE — only then “production-ready” |

---

## Explicit non-claims

- **Not LOCKED** for phases 15.5–20  
- **Not production-ready**  
- Do **not** self-APPROVE PR #25  
- Do **not** merge Phase 16 before 15.5 LOCKED on `main`

---

## Bottom line

Branch advances a **thorough MVP stack** through Phase 20 implementation. Integrity rules for self-service and outbox hold. Ship path remains: **15.5 lock → 16 lock → 17–20 CI/merge → 21–26**.
