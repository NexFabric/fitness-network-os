# Review Checkpoint — Main status

**Date:** 2026-08-12  
**Main HEAD:** `a7ee6d9` (PR #52) + open PR for 27.3  
**Alembic head:** `u4b5c6d7e8f9`

## Merged on main (truth)

| Band | Evidence |
|------|----------|
| Phase 8–15 | Historical PRs #13–#23 |
| Phase 15.5 | PR #25 → `125a8c6` |
| Phase 15.5 docs | PR #27 |
| Phase 16–26 MVP stack | PR #26 → `5046f10` |
| Health docs | PR #28 → `398e858` |
| Phase 27 UI/RBAC closure | PR #49 → `8b2904e` — role-guarded portals, `/me/session`, trainer assignment scope, federation `/admin/*`, PWA icon set, CSRF Bearer narrowing |
| Phase 27.2 ops console depth | PR #52 → `a7ee6d9` — devices, notifications, reports, staff, location edit, membership lifecycle |
| Phase 27.3 plan catalogue | open PR — `/plans` + `POST /memberships` (API-1), history endpoints (API-2) |
| Phase 27.1 device hardening | PR #49 → `8b2904e` — HMAC request signing + single-use nonce on the device channel (ADR-044), non-extractable `CryptoKey` on the scanner, CodeQL closure |

## Open / residual

| Item | Status |
|------|--------|
| PR #29 docs truth polish | may still open — optional |
| Phase 26 exit gate | **NOT PASSED** |
| Production-ready | **NO** |

## Current position

```text
main = 15.5 + 16–26 MVP + 27/27.1 production closure
Next = production depth (providers, full security/ops, exit PASS)
```

## Health (last control — 2026-08-12, local)

- `pytest` 311 passed · 1 skipped (local)  
- Playwright e2e **37 passed** (real Chromium, real backend), zero console errors across all 5 portals  
- ruff, mypy (85 files), `alembic check` (no drift), `check_permissions`, `check_permissions_db`, `check_tenancy`, `check_no_money_floats` PASS  
- admin-web + scanner-pwa builds PASS  
- CI on PR #49: every required check green. CodeQL carries one dismissed alert (`py/weak-sensitive-data-hashing` on `_hash_api_key`) — false positive for a 256-bit server-minted token, reasoning in the docstring  
- Dependabot: all 10 open alerts (vite/esbuild) are already fixed on this branch (vite 6.4.3, esbuild 0.25.12); they close when PR #49 lands  
- See `backend/docs/plans/CONTROL_HEALTH_REPORT.md`  
