# Phase 11 — Remove Money Floats

**Status:** CLOSING (PR #17)  
**Expand revision:** `f7a8b9c0d1e2`  
**Contract revision:** `g8b9c0d1e2f3` (deferred no-op until dual-column period ends)

## Goal

- No binary float for money  
- `amount_minor` + `currency` (or integer bps for rates)  
- EXPAND → BACKFILL → SWITCH → CONTRACT (no same-deploy DROP)

## Expand (this PR)

| Table | Legacy (kept) | New |
|-------|---------------|-----|
| opportunities | `value` Float | `value_amount_minor`, `currency` (default TRY) |
| retention_cockpit | `churn_probability` Float | `churn_probability_bps` 0..10000 |

Backfill:

- `value_amount_minor = ROUND(value * 100)::integer`  
- **Assumption:** historical Opportunity values are **TRY**  
- `churn_probability_bps = clamp(ROUND(prob * 10000), 0, 10000)`

ORM maps **only new columns**. Alembic `include_object` ignores drop noise for legacy float columns until CONTRACT.

## Contract (later PR)

Drop:

- `opportunities.value`  
- `retention_cockpit.churn_probability`  

Remove `LEGACY_EXPAND_COLUMNS` from `alembic/env.py`.

## Strict money boundary

- Schemas: `StrictInt` money / quantity fields  
- Services: `assert_amount_minor` / `assert_quantity` (no bare `int(float)`)  
- Helpers: `app/core/money.py` rejects float input  

## Tests

- Conversion: `legacy_major_string_to_minor` / `legacy_probability_to_bps`  
- Strict validation rejects `100.0`, `100.5`, `True`, `"100"`  
- Fitness script: no ORM Float columns  

## P1 follow-ups (not Phase 11 merge blockers)

- `BigInteger` for amount_minor globally  
- CONTRACT migration after one deploy cycle  
- Broader non-ORM float scanners  
