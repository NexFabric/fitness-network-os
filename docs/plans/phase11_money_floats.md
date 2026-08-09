# Phase 11 — Remove Money Floats

## Goal

Enforce MASTER_SPEC / AGENTS.md money rule:

- **No binary float for money**
- Prefer `amount_minor` (int) + `currency`
- Rates/probabilities that were float should use integer basis points where practical

## Audit summary (repo)

| Area | Status before Phase 11 | Action |
|------|------------------------|--------|
| Finance domain | `amount_minor` integers | None (already correct) |
| Membership prices / snapshots | integer minor | None |
| Entitlement wallet counters | integers | None |
| `Opportunity.value` | **Float** | → `value_amount_minor` + `currency` |
| `RetentionCockpit.churn_probability` | **Float** (analytics) | → `churn_probability_bps` (0–10000) |
| Frontend | No money float paths found | N/A |
| Conversion helpers | Missing | `app/core/money.py` (Decimal only) |

## Implementation

1. Migration `f7a8b9c0d1e2_phase11_remove_money_floats`
2. Model updates in `app/models/growth.py`
3. Fitness gate: `scripts/check_no_money_floats.py` (CI Lint job)
4. Tests: `tests/test_money_no_floats.py`

## CI gate

Lint job runs:

```bash
uv run python scripts/check_no_money_floats.py
```

Fails if any SQLAlchemy model column uses `Float` (ORM-level ban after Phase 11).

## Completion criteria

- [x] No money Float columns in models
- [x] Conversion helpers reject float input
- [x] Alembic constraints match models (no schema drift)
- [ ] PR #17 CI green + merge + main CI green → **Phase 11 LOCKED**

## Stop point for review

After Phase 11 merge readiness: **stop before Phase 12** (Idempotency Engine) for human review.
