# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–26)  
**Last updated:** 2026-08-10  
**Main HEAD:** `125a8c6` — Phase **15.5 LOCKED**  
**Alembic head on main:** `p9c0d1e2f3a4`  
**Active PR stack:** [#26](https://github.com/NexFabric/fitness-network-os/pull/26) Phase 16–20 MVP (not main)

**Hierarchy:** MASTER_SPEC → PRODUCTION_READINESS → this plan → PROGRESS_CHECKLIST → phase plans

**Do not claim production-ready** until Phase 26 CORE MVP EXIT GATE.

---

## Milestone map

| Phases | Theme | Status |
|--------|--------|--------|
| 0–7 | Core gate | 🟢 COMPLETED |
| 8–15 | Domain services | 🟢 LOCKED on main |
| 15.5 | Integrity closure | 🟢 **LOCKED** `125a8c6` |
| 16–20 | Notifications → Scanner PWA | 🟠 **on branch PR #26** |
| 21–26 | CI V2 → EXIT GATE | ⬜ / opening |

### Phase 15.5 — LOCKED

- PR #25 merge `125a8c6`
- Migrations: `n7a8b9c0d1e2`, `o8b9c0d1e2f3`, `p9c0d1e2f3a4`
- Trust: no public outbox/inbox; MEMBER `*:self`; event registry; outbox max-attempts DEAD
- Details: `backend/docs/plans/phase15_5_integrity_closure.md`

### Phase 16–20 — branch stack (not LOCKED)

See PR #26 and plans under `backend/docs/plans/phase16_*` … `phase20_*`.

### Phase 21–26 — next

CI V2 (frontend jobs), containers, HTTP security, observability, checklist automation, EXIT GATE.

## Non-negotiables

- Gym = tenant; RLS FORCE  
- Money: `amount_minor`  
- Domain → Outbox → Adapter (no Membership → WhatsApp)  
- No public generic outbox/inbox inject  
