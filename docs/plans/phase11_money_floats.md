# Phase 11 — Remove Money Floats

**Status:** 🟢 LOCKED / CI VERIFIED on main (merge `607b087`)  
**Phase 11 expand revision:** `f7a8b9c0d1e2` (EXPAND only; still no CONTRACT DROP)  
**Repo alembic head (2026-08-09):** `m6f7a8b9c0d1` (later phases advanced chain; Phase 11 expand body unchanged)

## Goal

- No binary float for money in ORM  
- `amount_minor` + `currency` (rates as integer bps)  
- EXPAND → BACKFILL → SWITCH → later CONTRACT (never DROP in same deploy)

## EXPAND (`f7a8b9c0d1e2`)

| Table | Legacy (kept) | New |
|-------|---------------|-----|
| opportunities | `value` Float | `value_amount_minor`, `currency` (default TRY) |
| retention_cockpit | `churn_probability` Float | `churn_probability_bps` 0..10000 |

Backfill SQL:

```sql
value_amount_minor = ROUND(value * 100)::integer
currency = TRY  -- historical assumption
churn_probability_bps = clamp(ROUND(churn_probability * 10000), 0, 10000)
```

ORM maps **only new columns**.  
`alembic/env.py` `LEGACY_EXPAND_COLUMNS` ignores drop-noise for the two legacy columns until CONTRACT.

## CONTRACT (future — NEW revision only)

When ready, generate a **new** Alembic revision from current head that:

```text
DROP opportunities.value
DROP retention_cockpit.churn_probability
```

and remove `LEGACY_EXPAND_COLUMNS` from `env.py`.

**Never edit an already-applied revision body to inject DROP.**

## PRE-PRODUCTION MIGRATION EXCEPTION

```text
Phase 11 is a pre-production migration exception.
Concurrent old-version application writers are NOT supported after expand.
This is NOT claimed as zero-downtime rolling dual-write compatibility.
The EXPAND/CONTRACT shape establishes the standard for future production migrations.
```

## Strict money boundary

- Schemas: `StrictInt` for money + `BasisPoints` for `percent_bps`  
- Services: `assert_amount_minor` / `assert_quantity`  
- Helpers: `app/core/money.py` rejects binary float  

## Tests

1. **Real migration test** (`tests/migrations/test_phase11_expand_migration.py`):  
   pre-Phase11 → seed Float rows → upgrade EXPAND → SELECT reconcile + row counts + legacy columns exist  

2. **Expand schema guard**: after head, both legacy and new columns present  

3. Helper / StrictInt unit tests  

## P1 follow-ups (not Phase 11 merge blockers)

- BigInteger for amount_minor  
- Real dual-write if/when production rolling deploys exist  
- CONTRACT revision after dual-column window  


## P2 audit note — legacy float conversion

Legacy binary-float CRM `Opportunity.value` values may contain historical IEEE-754 ambiguity.
Migrated `value_amount_minor` values are **best-effort normalized** and are **not** financial ledger amounts
(Payment/Invoice already used integer minor units). Tests allow ±1 minor unit on expansion reconciliation for this reason.
