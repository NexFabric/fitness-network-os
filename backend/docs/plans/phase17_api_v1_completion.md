# Phase 17 — Real API V1 Completion

**Status:** 🟠 **IN PROGRESS / IMPLEMENTED on branch** (17A landed) — **not LOCKED**  
**Plan path:** `backend/docs/plans/phase17_api_v1_completion.md`  
**Opened:** 2026-08-10 · **17A impl:** 2026-08-10 on `feat/phase16-notifications-reports`  
**Do not claim:** production-ready (Phase 26 exit gate only)

---

## Goal

Complete **real API V1** surface after integrity and operational domains are locked:

- Close MEMBER self-service gaps under `/api/v1/me/*` without reopening BOLA
- Fill staff/router gaps that block vertical-slice and Admin MVP (Phase 18–19)
- Align OpenAPI tags, response models, and authz documentation with what ships

**Not in scope for Phase 17:** new domain products (full check-in engine, documents, import, real notification providers, standalone workers). Prefer thin read/list/complete routes over new services.

---

## Prerequisites (merge gate)

| Gate | Requirement |
|------|-------------|
| **Phase 15.5** | **LOCKED on `main`** (APPROVE → merge → main CI green). `require_self` / `*:self` / no public outbox are source of truth. |
| **Phase 16** | **Preferred locked/merged** before 17 implementation lands on main. Stacked/parallel plan work OK; do not block 16 closeout. |
| **CI** | Unit/Integration + Security + Lint + tenancy gates green before claiming 17 waves done. |

Implementation of 17A may start on a feature branch after 15.5 is locked (or stacked carefully). **No LOCKED / CI VERIFIED claims** until merge + green main CI.

---

## Hard rules (from 15.5 integrity)

These are non-negotiable for all 17 waves:

1. **MEMBER BOLA closed pattern**
   - Never accept client-controlled `member_id` on self-service paths.
   - Resolve bound member: `current_user.id` → `members.user_id` (server-owned).
   - Authz: `AuthorizationService.require_self(..., "…:self", tenant_id, resource_owner_id=current_user.id)`.
2. **Permission naming**
   - Self routes use `*:self` grants already seeded (15.5C):  
     `memberships:read:self`, `checkins:read:self`, `checkins:write:self`,  
     `entitlements:read:self`, `entitlements:check:self` (check already wired).
   - Do **not** re-grant tenant-wide `memberships:read` / `entitlements:check` / etc. to MEMBER.
3. **Staff vs member**
   - Staff routes use `require_tenant` / coarse perms (`staff:read`, `members:read`, …).
   - User ≠ Member; staff link is not a membership.
4. **Domain boundaries**
   - No Membership → WhatsApp; notifications only via outbox path (Phase 16).
   - No public `/outbox` / `/inbox` reintroduction.
5. **Tenancy**
   - Tenant tables: `tenant_id` + index + RLS + tests; no float money fields.

Reference implementations:

- `POST /api/v1/me/entitlements/check` — `app/api/v1/endpoints/me.py`
- `POST /api/v1/access/qr/issue-self` — `app/api/v1/endpoints/access.py`
- Helpers: `AuthorizationService.require_self` / `require_tenant` — `app/core/authorization.py`

---

## Wave map

| Wave | Name | Outcome | Heavy impl? |
|------|------|---------|-------------|
| **17A** | `/me/*` expansion | MEMBER read surfaces: memberships, entitlements list/read, checkins **read** (if model exists); all `require_self` only | Medium (reads only) |
| **17B** | Staff router gaps | Missing list/get/update paths that block Admin MVP; least-privilege staff perms | Medium |
| **17C** | OpenAPI consistency | Tags, response models, error shapes, permission docs aligned with routers | Light–medium |

---

## 17A — `/me/*` expansion (`require_self` only)

**Status:** 🟠 **IMPLEMENTED on branch** (2026-08-10) — **not LOCKED**  
**Depends on:** 15.5 LOCKED for main merge; 16 merge preferred (no hard code dependency for `/me` reads)  
**Code:** `backend/app/api/v1/endpoints/me.py` · tests `backend/tests/api/test_me_self_service.py`

### Existing / landed routes (17A)

| Method | Path | Perm | Notes |
|--------|------|------|--------|
| `GET` | `/api/v1/me/profile` | `profile:read` + owner | Thin self profile (user + bound member). No `profile:read:self` seed — authorize with `resource_owner_id=current_user.id` |
| `GET` | `/api/v1/me/member` | `memberships:read:self` | Bound member card |
| `GET` | `/api/v1/me/memberships` | `memberships:read:self` | List memberships for **bound** member only; no path `member_id` |
| `GET` | `/api/v1/me/entitlements` | `entitlements:read:self` | Wallet snapshot (no consume) |
| `GET` | `/api/v1/me/checkins` | `checkins:read:self` | List own `Checkin` rows (read-only; no write product) |
| `POST` | `/api/v1/me/entitlements/check` | `entitlements:check:self` | Pre-existing; regression-tested |
| `POST` | `/api/v1/access/qr/issue-self` | `access:issue:self` | Same bind pattern (not under `/me` prefix) |

### Explicit non-goals (17A)

- Full check-in **write** product, anti-passback, attendance rules (`checkins:write:self` may stay unused until later phase)
- Staff impersonation of member under `/me`
- Accepting `member_id` / `user_id` in body or path for “self”
- Re-opening MEMBER grants to tenant-wide read permissions

### Implementation pattern (sketch)

```text
require_self(user, "{resource}:…:self", tenant_id, resource_owner_id=user.id)
member = MemberService.get_member_by_user_id(tenant_id, user.id)
if member is None → 404 member_not_bound
query/list only where member_id == member.id AND tenant_id == tenant_id
```

### Tests (minimum for 17A)

- MEMBER A ALLOW on own `/me/*` reads
- MEMBER A DENY when attempting staff path for member B (existing BOLA suite remains green)
- MEMBER with no bound member → 404 `member_not_bound` (not empty leak of other members)
- Staff without `*:self` may 403 on `/me` (or document intentional dual path if staff also have self grants)
- Cross-tenant isolation still holds under RLS

### Exit criteria (17A)

- [x] Routes live under `me` router; no client `member_id` (on branch)
- [x] `*:self` routes use `require_self`; profile uses careful owner + tenant check
- [x] API tests green on isolated PG (branch)
- [ ] No LOCKED claim until main merge + CI

---

## 17B — Staff router gaps

**Status:** planned after 17A (or parallel only if no file conflict)  
**Depends on:** 15.5 LOCKED; 16 preferred

### Intent

Close **API completeness** holes for staff/admin clients without inventing new domains.

### Likely gap areas (inventory at implementation time)

Audit routers under `backend/app/api/v1/endpoints/` against services:

| Area | Today (approx.) | Typical gaps |
|------|-----------------|--------------|
| Memberships | Lifecycle posts (freeze/cancel/…) | list/get by member or id if service supports |
| Members | CRUD + tags/notes/consent | pagination, filters consistency |
| Finance | create/issue flows | list invoices/payments for ops UI |
| Staff | link/list/get | deactivate/unlink if product needs |
| Locations | create/list/update | facilities deferred (Phase 14) |
| Access | issue/validate/keys | device/heartbeat still MODEL |
| Notifications/Reports | Phase 16 staff APIs | member prefs deferred |

**Rule:** prefer wiring existing service methods; avoid new tables in 17B unless a trivial expand-only is already required by UI contract.

### Authz

- Use `require_tenant` / `_require(..., "resource:action")` — never `*:self` for cross-member staff paths
- TRAINER → assigned-members-only remains **deferred** (15.5 deferred list) unless a cheap existing link model allows it

### Exit criteria (17B)

- [ ] Documented gap list closed or explicitly deferred with reason
- [ ] RBAC matrix unchanged for MEMBER least privilege
- [ ] Tests for new staff routes + tenancy

---

## 17C — OpenAPI consistency

**Status:** planned after or alongside 17B  
**Depends on:** 17A/17B routes stable enough to document

### Intent

Make generated OpenAPI / FastAPI metadata match reality for Admin Web and Scanner consumers:

- Consistent `tags` (`me`, `memberships`, `staff`, …)
- Response models for list/get (no bare `dict` where avoidable)
- Error `detail` codes documented where already used (`member_not_bound`, security 403 shape)
- Permission requirements noted in route docstrings (source of truth remains `permissions.yml` + seed)
- No public outbox/inbox operations in schema

### Exit criteria (17C)

- [ ] OpenAPI export review (manual or CI smoke) without orphan/ghost paths
- [ ] `/me` and staff gap routes appear with correct methods and models

---

## Residual / known risks (carry into implementation)

| ID | Risk | Mitigation |
|----|------|------------|
| R17-001 | `profile:read` is **not** `profile:read:self`; latent MEMBER fallback in `is_authorized` for non-self names | Prefer migrate to `profile:read:self` + `require_self` before `GET /me` profile; or skip profile stub in 17A |
| R17-002 | Check-in model may be thin/absent | Read-only if exists; else defer product to later phase — do not invent full attendance in 17 |
| R17-003 | Parallel Phase 16 agents | Prefer docs-only / separate branch until 16 merge; avoid fighting dirty notification/report files |
| R17-004 | Claiming completeness too early | Checklist stays “plan opened / in progress”; LOCKED only after main CI |

---

## Suggested sequencing

```text
15.5 LOCKED on main
  → 16 merge preferred (notifications/reports staff APIs stable)
  → 17A /me reads (memberships, entitlements; checkins if ready)
  → 17B staff gaps (inventory-driven)
  → 17C OpenAPI polish
  → Phase 18 Executable vertical slice E2E
```

Parallel **planning** of 17A while 16 closes is intentional and allowed.

---

## Out of scope (later phases)

- Phase 18: E2E vertical slice  
- Phase 19–20: Admin Web / Scanner PWA  
- Documents, import engine, real channel providers, standalone worker productization  
- Full check-in product, anti-passback, offline gateway  

---

## Exit criteria (Phase 17 overall)

- [ ] 17A–C exit items satisfied or explicitly deferred with checklist note  
- [ ] No MEMBER BOLA regression (`*:self` + bound member only)  
- [ ] CI green on PR; merge to main → then **LOCKED** (not before)  
- [ ] Progress checklist updated honestly (no production-ready claim)  

---

## File touch map (expected when implementing)

| Path | Wave |
|------|------|
| `backend/app/api/v1/endpoints/me.py` | 17A |
| `backend/app/api/v1/endpoints/*.py` (staff gaps) | 17B |
| `backend/tests/api/test_*me*` / BOLA suite extensions | 17A |
| OpenAPI / router metadata | 17C |
| `docs/PROGRESS_CHECKLIST.md` | status only |

No Alembic expected for pure route completion unless a missing index/permission is discovered (then expand-only + YAML parity).
