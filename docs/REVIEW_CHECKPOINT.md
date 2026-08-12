# Review Checkpoint — Main status

**Date:** 2026-08-12  
**Branch HEAD (PR #49):** `6f8c853`  
**Alembic head:** `u4b5c6d7e8f9`

## Merged on main (truth)

| Band | Evidence |
|------|----------|
| Phase 8–15 | Historical PRs #13–#23 |
| Phase 15.5 | PR #25 → `125a8c6` |
| Phase 15.5 docs | PR #27 |
| Phase 16–26 MVP stack | PR #26 → `5046f10` |
| Health docs | PR #28 → `398e858` |
| Phase 27 UI/RBAC closure | `feat/phase27-ui-production-closure` (PR #49, **open**) — role-guarded portals, `/me/session`, trainer assignment scope, federation `/admin/*`, PWA icon set, CSRF Bearer narrowing |
| Phase 27.1 device hardening | same branch — HMAC request signing + single-use nonce on the device channel (ADR-044), non-extractable `CryptoKey` on the scanner, CodeQL closure |

## Open / residual

| Item | Status |
|------|--------|
| PR #49 merge | **blocked on human review** — `main` requires 1 approving review and `enforce_admins` is on; the author cannot self-approve |
| PR #29 docs truth polish | may still open — optional |
| Phase 26 exit gate | **NOT PASSED** |
| Production-ready | **NO** |

## Current position

```text
main = 15.5 + 16–24 MVP + exit-gate docs
Next = production depth (providers, full security/ops, exit PASS)
```

## Health (last control — 2026-08-12, local)

- `pytest` 301 passed · 1 skipped (local **and** CI on `6f8c853`)  
- Playwright e2e 21 passed (real Chromium, real backend), zero console errors across all 5 portals  
- ruff, mypy (85 files), `alembic check` (no drift), `check_permissions`, `check_permissions_db`, `check_tenancy`, `check_no_money_floats` PASS  
- admin-web + scanner-pwa builds PASS  
- CI on PR #49: every required check green. CodeQL carries one dismissed alert (`py/weak-sensitive-data-hashing` on `_hash_api_key`) — false positive for a 256-bit server-minted token, reasoning in the docstring  
- Dependabot: all 10 open alerts (vite/esbuild) are already fixed on this branch (vite 6.4.3, esbuild 0.25.12); they close when PR #49 lands  
- See `backend/docs/plans/CONTROL_HEALTH_REPORT.md`  
