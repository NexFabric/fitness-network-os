# Load harness

These k6 scripts are **capacity rehearsal**, not a claimed production SLO.
Running them against staging is evidence. Checking them in is not.

Default VUs are CI-safe (50). Raise `VUS` for a real rehearsal.

```bash
# against a reachable API (auth token + tenant required)
export BASE_URL=https://api.staging.example.com
export AUTH_TOKEN=...
export TENANT_ID=...
k6 run ops/load/qr_validate.js
k6 run ops/load/class_book.js
k6 run ops/load/finance_idempotency.js
```

Do not add these as a required GitHub check. A required load job against
an ephemeral CI stack is expensive and does not measure production.
