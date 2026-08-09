# Phase 14 — Member / Gym Core Completion

**Status:** 🟢 LOCKED (PR #21 merge `e332cf5`)  
**Depends on:** Phase 13 LOCKED (QR & Access)  
**Migration:** `k4d5e6f7a8b9` (member_number/staff uniqueness + permissions)

## Scope

Promote Wave 1 gym-core models from MODEL-only to service + API:

| Area | Capability |
|------|------------|
| Members | Create / get / list / update / status transitions |
| Tags & Notes | Member 360 annotations |
| Locations | Create / list / update branches |
| Staff | Link platform User → tenant Staff (+ optional location) |
| Consent | Record grant/withdraw (definition catalog) |

## Rules

- Gym = tenant; all tables already RLS-backed
- `UNIQUE(tenant_id, member_number)` expand
- `UNIQUE(tenant_id, user_id)` on staff (one staff row per user per gym)
- Services flush-only; API commits
- User ≠ Member (staff links User; members are gym profiles)

## Deferred

- Documents / secure file storage (ADR-034)
- Import engine
- Full PII classification engine / encryption fields
- Facilities sub-resources beyond Location

## Exit

- Real PG service tests
- Permissions seed + API routers
- CI green
