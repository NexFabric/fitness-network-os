# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–26)  
**Hierarchy (agents must follow):**

```text
MASTER_SPEC
  → PRODUCTION_READINESS
    → IMPLEMENTATION_MASTER_PLAN  (this file)
      → PROGRESS_CHECKLIST
        → active phase plan (docs/plans/phaseN_*.md)
```

Do **not** infer progress from obsolete foundation-only notes. Use `docs/PROGRESS_CHECKLIST.md` for maturity.

---

## Milestone map

| Phases | Theme | Status (see checklist) |
|--------|--------|-------------------------|
| 0–7 | Core gate / security / RLS / RBAC | COMPLETED (gate closure) |
| 8 | Membership domain | CI VERIFIED |
| 9 | Entitlement engine | CI VERIFIED (P1 prep before 13) |
| 10 | Finance domain | CI VERIFIED (P1 audit ledger) |
| 11 | Remove money floats | 🟢 LOCKED (PR #17) |
| 12 | Real idempotency engine | 🟢 LOCKED (PR #19 merge `227f42e`) |
| 13 | QR & access engine | 🟢 LOCKED (PR #20 merge `babc33c`) |
| 14 | Member / gym core | **IN PROGRESS** |
| 15 | Outbox / inbox / jobs | After 14 |
| 16 | Notifications & reports API | |
| 17 | Real API V1 routers completion | |
| 18 | Vertical slice E2E | |
| 19–20 | Admin Web / Scanner PWA MVP | |
| 21–26 | CI V2, hardening, observability, exit gate | |

---

## Phase 11 (final closure on PR #17)

- Expand-only migration head: `f7a8b9c0d1e2` (add + backfill; **no DROP**)  
- CONTRACT: create a **new** revision later — never edit applied expand body  
- Pre-production exception: no concurrent old/new app writers claimed  
- Historical Opportunity currency: **TRY**  
- Strict API money + BasisPoints; service `assert_amount_minor`  
- Real PG migration reconciliation test + expand schema guard  
- Details: `docs/plans/phase11_money_floats.md`

## Phase 12 — LOCKED

- `IdempotencyRecord` UNIQUE(tenant_id, operation, key) + request_hash + lease  
- Flush-only service + `run_idempotent` UoW  
- Wired: finance invoice/payment/refund/credit + entitlement consume  
- Details: `backend/docs/plans/phase12_idempotency.md`

## Phase 13 — LOCKED

- Short-lived signed QR (`exp`+`jti` required); HMAC local ref / future KMS  
- Key lifecycle ACTIVE → VERIFY_ONLY → REVOKED  
- `qr_jti_replays` tenant-scoped replay protection  
- Validate → entitlement check → AccessAttempt (+ Checkin)  
- Details: `backend/docs/plans/phase13_qr_access.md`

## Phase 14 (active)

- Member CRUD + status transitions, tags/notes, consent records  
- Locations + Staff user linking (User ≠ Member)  
- UNIQUE(tenant_id, member_number), UNIQUE(tenant_id, user_id) on staff  
- Details: `backend/docs/plans/phase14_member_gym_core.md`  

## Non-negotiables

- Gym = tenant; RLS FORCE on tenant tables  
- Money: `amount_minor` int (never binary float)  
- Expand → backfill → switch → contract for destructive schema  
- Domain boundaries (no Membership → WhatsApp shortcuts)  

## Foundation archive (COMPLETED)

Repository bootstrap, Docker, FastAPI factory, SQLAlchemy/Alembic, org/tenant, auth/MFA foundation, RLS helpers, RBAC matrix, audit model, CI gates — complete under Phase 0–7. Historical detail remains in git history and older docs; do not treat foundation section as the active execution plan.
