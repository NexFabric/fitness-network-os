# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–26)  
**Last updated:** 2026-08-10  
**Main HEAD:** `125a8c6` (Phase 15.5 LOCKED)  
**Alembic head on main:** `p9c0d1e2f3a4`  
**Active stack:** Phase 16–20 on PR [#26](https://github.com/NexFabric/fitness-network-os/pull/26) — **not LOCKED**

**Hierarchy (agents must follow):**

```text
MASTER_SPEC
  → PRODUCTION_READINESS
    → IMPLEMENTATION_MASTER_PLAN  (this file)
      → PROGRESS_CHECKLIST
        → active phase plan (docs/plans/phaseN_*.md or backend/docs/plans/)
```

Do **not** infer progress from obsolete foundation-only notes. Use `docs/PROGRESS_CHECKLIST.md` for maturity.

**Next formal step:** Merge Phase **16+** stack (PR #26 after review) → then Phase **21** CI V2 full verification → 22–26.  
**Do not claim production-ready** until Phase 26 CORE MVP EXIT GATE.

---

## Milestone map

| Phases | Theme | Status (see checklist) |
|--------|--------|-------------------------|
| 0–7 | Core gate / security / RLS / RBAC | 🟢 COMPLETED (gate closure) |
| 8 | Membership domain | 🟢 CI VERIFIED / LOCKED (PR #13) |
| 9 | Entitlement engine | 🟢 CI VERIFIED / LOCKED (PR #14) |
| 10 | Finance domain | 🟢 CI VERIFIED / LOCKED (PR #15) |
| 11 | Remove money floats | 🟢 LOCKED (PR #17 merge `607b087`) |
| 12 | Real idempotency engine | 🟢 LOCKED (PR #19 merge `227f42e`) |
| 13 | QR & access engine | 🟢 LOCKED (PR #20 merge `babc33c`) |
| 14 | Member / gym core | 🟢 LOCKED (PR #21 merge `e332cf5`) |
| 15 | Outbox / inbox / jobs | 🟢 LOCKED (PR #22 merge `67b8214`) |
| 15.5 | Cross-cutting integrity closure | 🟢 **CI VERIFIED / LOCKED** (PR #25 merge `125a8c6`) |
| 16 | Notifications & reports API | 🟡 branch (PR #26) — not LOCKED |
| 17 | Real API V1 routers completion | 🟡 branch — not LOCKED |
| 18 | Vertical slice E2E | 🟡 branch — not LOCKED |
| 19–20 | Admin Web / Scanner PWA MVP | 🟡 branch — not LOCKED |
| 21–26 | CI V2, hardening, observability, exit gate | ⬜ starting (21–23 skeleton) |

---

## Locked phase notes (summary)

### Phase 11 — LOCKED

- Expand-only migration head: `f7a8b9c0d1e2` (add + backfill; **no DROP**)  
- CONTRACT: create a **new** revision later — never edit applied expand body  
- Pre-production exception: no concurrent old/new app writers claimed  
- Historical Opportunity currency: **TRY**  
- Strict API money + BasisPoints; service `assert_amount_minor`  
- Details: `docs/plans/phase11_money_floats.md`

### Phase 12 — LOCKED

- `IdempotencyRecord` UNIQUE(tenant_id, operation, key) + request_hash + lease  
- Flush-only service + `run_idempotent` UoW  
- Wired: finance invoice/payment/refund/credit + entitlement consume  
- Details: `backend/docs/plans/phase12_idempotency.md`

### Phase 13 — LOCKED

- Short-lived signed QR (`exp`+`jti` required); HMAC local ref / future KMS  
- Key lifecycle ACTIVE → VERIFY_ONLY → REVOKED  
- `qr_jti_replays` tenant-scoped replay protection  
- Validate → entitlement check → AccessAttempt (+ Checkin)  
- Details: `backend/docs/plans/phase13_qr_access.md`

### Phase 14 — LOCKED

- Member CRUD + status transitions, tags/notes, consent records  
- Locations + Staff user linking (User ≠ Member)  
- UNIQUE(tenant_id, member_number), UNIQUE(tenant_id, user_id) on staff  
- Details: `backend/docs/plans/phase14_member_gym_core.md`

### Phase 15 — LOCKED

- Transactional outbox enqueue/claim/publish with `FOR UPDATE SKIP LOCKED`  
- Inbox exactly-once receive + handler dispatch  
- Expand: attempt_count, available_at, dedupe_key; UNIQUE(tenant_id, event_id)  
- Details: `backend/docs/plans/phase15_outbox_inbox.md`

### Phase 15.5 — LOCKED (main `125a8c6`)

**PR #25** merged as `125a8c6` · alembic head `p9c0d1e2f3a4` · 🟢 CI VERIFIED / LOCKED.

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

### Phase 16 — ACTIVE ON BRANCH (not LOCKED)

- Notification templates / deliveries service + API (PR #26)  
- Report definitions / runs (export hooks)  
- Prefer Outbox for async delivery; domain → Event → Notification (no WhatsApp shortcuts)  
- No generic public `/inbox` reintroduction; provider webhooks only  
- **Do not mark LOCKED** until merge to main + green required CI  

### Phase 21+ — next hardening track (after 16–20 merge path)

- Phase 21: CI V2 — frontend admin-web + scanner-pwa build jobs; keep backend gates  
- Phase 22: Production container hardening checklist / Dockerfile improvements  
- Phase 23: HTTP security baseline (CORS allowlist, security headers)  
- Phase 24–26: observability, checklist truth model, CORE MVP EXIT GATE  

---

## Non-negotiables

- Gym = tenant; RLS FORCE on tenant tables  
- Money: `amount_minor` int (never binary float)  
- Expand → backfill → switch → contract for destructive schema  
- Domain boundaries (no Membership → WhatsApp shortcuts)  
- Transactional outbox + idempotency on money/entitlement mutations  
- No public generic outbox/inbox HTTP reintroduction  

## Foundation archive (COMPLETED)

Repository bootstrap, Docker, FastAPI factory, SQLAlchemy/Alembic, org/tenant, auth/MFA foundation, RLS helpers, RBAC matrix, audit model, CI gates — complete under Phase 0–7. Historical detail remains in git history and older docs; do not treat foundation section as the active execution plan.
