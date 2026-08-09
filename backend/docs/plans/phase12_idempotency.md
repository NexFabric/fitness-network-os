# Phase 12 — Real Idempotency Engine

**Status:** IN PROGRESS (`feat/phase12-idempotency-engine`)

## Design

```text
IdempotencyRecord
  tenant_id + operation + key  UNIQUE
  request_hash (sha256 canonical JSON)
  status: PROCESSING | SUCCEEDED | FAILED
  response_status / response_body
  locked_until + owner_token (lease)
  expires_at, attempt_count
```

## Semantics

| Case | Result |
|------|--------|
| First claim | PROCEED |
| Same hash SUCCEEDED | REPLAY cached body |
| Different hash | CONFLICT 409 IDEMPOTENCY_CONFLICT |
| PROCESSING + active lease | IN_PROGRESS + Retry-After |
| PROCESSING + expired lease + same hash | reclaim PROCEED |
| Cross-tenant same key | independent |

## Architecture

- `IdempotencyService` (flush only)
- `run_idempotent` UoW helper for APIs
- Domain services still flush; UoW commits
- Domain-level unique keys remain defense in depth

## Integrated operations

- `finance.invoice.create` (when Idempotency-Key present)
- `finance.payment.create`
- `finance.refund.create`
- `finance.credit.issue`
- `entitlements.consume`

## Tests

`tests/services/test_idempotency.py` — real PostgreSQL.

## Deferred

- 100-way concurrent stress in CI (optional later)
- Full middleware auto-intercept (prefer explicit UoW)
