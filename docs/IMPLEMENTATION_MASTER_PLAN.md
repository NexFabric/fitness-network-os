# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–26)  
**Last updated:** 2026-08-10  
**Main HEAD (docs sync base):** `af8f809`  
**PR #25 head (15.5):** `ffba0a8`  
**Alembic head (15.5 branch):** `p9c0d1e2f3a4`

**Hierarchy (agents must follow):**

```text
MASTER_SPEC
  → PRODUCTION_READINESS
    → IMPLEMENTATION_MASTER_PLAN  (this file)
      → PROGRESS_CHECKLIST
        → active phase plan (docs/plans/phaseN_*.md or backend/docs/plans/)
```

Do **not** infer progress from obsolete foundation-only notes. Use `docs/PROGRESS_CHECKLIST.md` for maturity.

**Next formal step:** Phase **15.5** PR #25 → independent APPROVE → merge → main CI → **LOCKED** → then **16 Notifications & Reports**  
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
| 15.5 | Cross-cutting integrity closure | 🟡 **PR CI GREEN** (`ffba0a8`) — not LOCKED until merge |
| 16 | Notifications & reports API | ⬜ after 15.5 LOCKED |
| 17 | Real API V1 routers completion | ⬜ |
| 18 | Vertical slice E2E | ⬜ |
| 19–20 | Admin Web / Scanner PWA MVP | ⬜ |
| 21–26 | CI V2, hardening, observability, exit gate | ⬜ |

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

### Phase 15.5 — MERGE GATE OPEN (not LOCKED)

**PR #25** head `ffba0a8` · alembic `p9c0d1e2f3a4` · PR CI green as of 2026-08-10.

Delivered on branch (do not treat as main LOCKED yet):

- RBAC `permissions.yml` ↔ DB parity (missing + extra grants)  
- Idempotency business savepoint + FAILED same-hash only  
- Outbox lease reclaim + worker CAS fencing + max-attempt crash-loop → DEAD  
- Inbox savepoint + FAILED retry  
- Event envelope v1 + **canonical event_type registry** on enqueue  
- Finance allocation reversals + immutable triggers; ledger RESTRICT  
- No public generic `/outbox` HTTP inject; GYM_* lack outbox/inbox write  
- MEMBER BOLA closed: `*:self` + `/me` + authz owner proof for self perms  

**Remaining formal gates:** independent human APPROVE → merge → main CI green → docs LOCKED.

Details: `backend/docs/plans/phase15_5_integrity_closure.md`

### Phase 16 — AFTER 15.5 LOCKED (not started)

- Notification templates / deliveries service + API  
- Report definitions / runs (export hooks)  
- Prefer Outbox for async delivery; domain → Event → Notification (no WhatsApp shortcuts)  
- No generic public `/inbox` reintroduction; provider webhooks only  

---

## Non-negotiables

- Gym = tenant; RLS FORCE on tenant tables  
- Money: `amount_minor` int (never binary float)  
- Expand → backfill → switch → contract for destructive schema  
- Domain boundaries (no Membership → WhatsApp shortcuts)  
- Transactional outbox + idempotency on money/entitlement mutations  

## Foundation archive (COMPLETED)

Repository bootstrap, Docker, FastAPI factory, SQLAlchemy/Alembic, org/tenant, auth/MFA foundation, RLS helpers, RBAC matrix, audit model, CI gates — complete under Phase 0–7. Historical detail remains in git history and older docs; do not treat foundation section as the active execution plan.
