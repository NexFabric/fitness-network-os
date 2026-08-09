# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–26)  
**Last updated:** 2026-08-10  
**Main HEAD:** `125a8c6` (Phase 15.5 MERGED / CI VERIFIED)  
**Alembic head on main:** `p9c0d1e2f3a4`  
**Active stack:** Phase 16–25 on PR [#26](https://github.com/NexFabric/fitness-network-os/pull/26) — **IMPLEMENTED / PARTIAL on branch; not on main**

**Hierarchy (agents must follow):**

```text
MASTER_SPEC
  → PRODUCTION_READINESS
    → IMPLEMENTATION_MASTER_PLAN  (this file)
      → PROGRESS_CHECKLIST
        → active phase plan (docs/plans/phaseN_*.md or backend/docs/plans/)
```

Do **not** infer progress from obsolete foundation-only notes. Use `docs/PROGRESS_CHECKLIST.md` for maturity.

**Next formal step:** Merge Phase **16+** stack (PR #26 after review + green CI) → deepen 21–24 as needed → re-score Phase **26**.  
**Do not claim production-ready** until Phase 26 CORE MVP EXIT GATE is **PASS**.

Truth model: `backend/docs/plans/phase25_checklist_truth.md`  
Exit gate: `backend/docs/plans/phase26_core_mvp_exit_gate.md` — **FAIL / NOT PASSED**

---

## Milestone map

| Phases | Theme | Status (see checklist) |
|--------|--------|-------------------------|
| 0–7 | Core gate / security / RLS / RBAC | 🟢 COMPLETED (gate closure) |
| 8 | Membership domain | 🟢 MERGED / CI VERIFIED (PR #13) |
| 9 | Entitlement engine | 🟢 MERGED / CI VERIFIED (PR #14) |
| 10 | Finance domain | 🟢 MERGED / CI VERIFIED (PR #15) |
| 11 | Remove money floats | 🟢 MERGED (PR #17 merge `607b087`) |
| 12 | Real idempotency engine | 🟢 MERGED (PR #19 merge `227f42e`) |
| 13 | QR & access engine | 🟢 MERGED (PR #20 merge `babc33c`) |
| 14 | Member / gym core | 🟢 MERGED (PR #21 merge `e332cf5`) |
| 15 | Outbox / inbox / jobs | 🟢 MERGED (PR #22 merge `67b8214`) |
| 15.5 | Cross-cutting integrity closure | 🟢 **MERGED / CI VERIFIED** (PR #25 merge `125a8c6`) |
| 16 | Notifications & reports API | 🟡 **IMPLEMENTED on PR #26** — not on main |
| 17 | Real API V1 routers completion | 🟡 **PARTIAL on PR #26** (17A done; 17B/17C open) |
| 18 | Vertical slice E2E | 🟡 **PARTIAL on PR #26** (service e2e; HTTP deferred) |
| 19–20 | Admin Web / Scanner PWA MVP | 🟡 **IMPLEMENTED scaffold on PR #26** |
| 21–24 | CI V2, container, HTTP, observability | 🟡 **PARTIAL light MVP on PR #26** |
| 25 | Checklist truth model | 🟡 **IMPLEMENTED on branch** (docs) |
| 26 | CORE MVP EXIT GATE | 🔴 **FAIL / NOT PASSED** — **not production-ready** |

---

## Locked / merged phase notes (summary)

### Phase 11 — MERGED

- Expand-only migration head: `f7a8b9c0d1e2` (add + backfill; **no DROP**)  
- CONTRACT: create a **new** revision later — never edit applied expand body  
- Pre-production exception: no concurrent old/new app writers claimed  
- Historical Opportunity currency: **TRY**  
- Strict API money + BasisPoints; service `assert_amount_minor`  
- Details: `docs/plans/phase11_money_floats.md`

### Phase 12 — MERGED

- `IdempotencyRecord` UNIQUE(tenant_id, operation, key) + request_hash + lease  
- Flush-only service + `run_idempotent` UoW  
- Wired: finance invoice/payment/refund/credit + entitlement consume  
- Details: `backend/docs/plans/phase12_idempotency.md`

### Phase 13 — MERGED

- Short-lived signed QR (`exp`+`jti` required); HMAC local ref / future KMS  
- Key lifecycle ACTIVE → VERIFY_ONLY → REVOKED  
- `qr_jti_replays` tenant-scoped replay protection  
- Validate → entitlement check → AccessAttempt (+ Checkin)  
- Details: `backend/docs/plans/phase13_qr_access.md`

### Phase 14 — MERGED

- Member CRUD + status transitions, tags/notes, consent records  
- Locations + Staff user linking (User ≠ Member)  
- UNIQUE(tenant_id, member_number), UNIQUE(tenant_id, user_id) on staff  
- Details: `backend/docs/plans/phase14_member_gym_core.md`

### Phase 15 — MERGED

- Transactional outbox enqueue/claim/publish with `FOR UPDATE SKIP LOCKED`  
- Inbox exactly-once receive + handler dispatch  
- Expand: attempt_count, available_at, dedupe_key; UNIQUE(tenant_id, event_id)  
- Details: `backend/docs/plans/phase15_outbox_inbox.md`

### Phase 15.5 — MERGED (main `125a8c6`)

**PR #25** merged as `125a8c6` · alembic head `p9c0d1e2f3a4` · 🟢 CI VERIFIED / MERGED.

Delivered and on main:

- RBAC `permissions.yml` ↔ DB parity (missing + extra grants)  
- Idempotency business savepoint + FAILED same-hash only  
- Outbox lease reclaim + worker CAS fencing + max-attempt crash-loop → DEAD  
- Inbox savepoint + FAILED retry  
- Event envelope v1 + **canonical event_type registry** on enqueue  
- Finance allocation reversals + immutable triggers; ledger RESTRICT  
- No public generic `/outbox` HTTP inject; GYM_* lack outbox/inbox write  
- MEMBER BOLA closed: `*:self` + `/me` + authz owner proof for self perms  

Details: `backend/docs/plans/phase15_5_integrity_closure.md`

### Phase 16–20 — ACTIVE ON BRANCH (not on main)

- **16:** Notification templates/deliveries + report definitions/runs; log provider; outbox path (PR #26)  
- **17:** 17A `/me/*` self-service expansion; 17B/17C still open  
- **18:** Service-layer vertical slice e2e (HTTP E2E deferred)  
- **19–20:** Admin-web + scanner-pwa MVP scaffolds  
- **Do not mark MERGED** until merge to main + green required CI  

### Phase 21–26 — hardening / truth / exit (branch)

| Phase | Honest status |
|-------|----------------|
| 21 CI V2 | PARTIAL — frontend `admin-web` + `scanner-pwa` build jobs |
| 22 Containers | PARTIAL — `backend/Dockerfile.prod` multi-stage non-root |
| 23 HTTP security | PARTIAL — prod CORS allowlist + basic headers |
| 24 Observability | PARTIAL stub — request/correlation id + access log |
| 25 Checklist truth | IMPLEMENTED on branch — `phase25_checklist_truth.md` |
| 26 Exit gate | **FAIL / NOT PASSED** — `phase26_core_mvp_exit_gate.md` |

---

## Non-negotiables

- Gym = tenant; RLS FORCE on tenant tables  
- Money: `amount_minor` int (never binary float)  
- Expand → backfill → switch → contract for destructive schema  
- Domain boundaries (no Membership → WhatsApp shortcuts)  
- Transactional outbox + idempotency on money/entitlement mutations  
- No public generic outbox/inbox HTTP reintroduction  
- **Not production-ready** until Phase 26 PASS  

## Foundation archive (COMPLETED)

Repository bootstrap, Docker, FastAPI factory, SQLAlchemy/Alembic, org/tenant, auth/MFA foundation, RLS helpers, RBAC matrix, audit model, CI gates — complete under Phase 0–7. Historical detail remains in git history and older docs; do not treat foundation section as the active execution plan.
