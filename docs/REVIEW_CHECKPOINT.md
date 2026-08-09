# Review Checkpoint — Phase 12 LOCKED / Phase 13 active

**Date:** 2026-08-09  
**Purpose:** Track sequential locks through Phase 13 (QR & Access).

## Locked / CI verified on `main`

| Phase | PR | main merge | Status |
|-------|-----|------------|--------|
| Phase 8 Membership | [#13](https://github.com/NexFabric/fitness-network-os/pull/13) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 9 Entitlements | [#14](https://github.com/NexFabric/fitness-network-os/pull/14) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 10 Finance | [#15](https://github.com/NexFabric/fitness-network-os/pull/15) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 11 Money floats | [#17](https://github.com/NexFabric/fitness-network-os/pull/17) | `607b087` | 🟢 LOCKED / CI VERIFIED |
| Phase 12 Idempotency | [#19](https://github.com/NexFabric/fitness-network-os/pull/19) | `227f42e` | 🟢 LOCKED / CI VERIFIED |

## Phase 13 — IN PROGRESS

- Branch: `feat/phase13-qr-access-engine`
- Short-lived HMAC QR, jti replay, key rotation, AccessAttempt/Checkin
- Plan: `backend/docs/plans/phase13_qr_access.md`

## Do not start yet

- Phase 14+ (Member core, Outbox, etc.) until Phase 13 LOCKED

## Local verification notes

- Postgres test DB often on Docker port **5433**  
