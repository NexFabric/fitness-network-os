# Review Checkpoint — Main status

**Date:** 2026-08-13  
**Main HEAD:** `2a1002d`; no open PRs
**Alembic head:** `v5c6d7e8f9a0`

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
| Phase 27.3 plan catalogue | PR #53 → `a60d55c` — `/plans` + `POST /memberships` (API-1), delivery/run history (API-2) |
| Phase 27.1 device hardening | PR #49 → `8b2904e` — HMAC request signing + single-use nonce on the device channel (ADR-044), non-extractable `CryptoKey` on the scanner, CodeQL closure |
| Phase 27.4 production closure | PR #55 → `2a1002d` — privileged MFA enrollment + session rotation, private S3/MinIO report storage, real Prometheus metrics, frozen non-root image, required Playwright gate |

## Open / residual

| Item | Status |
|------|--------|
| PR #29 docs truth polish | may still open — optional |
| Phase 26 exit gate | **NOT PASSED** |
| Production-ready | **NO** |

## Current position

```text
main = 15.5 + 16–26 MVP + 27/27.1/27.2/27.3/27.4
Next = restore/PITR drill + real S3 staging proof + independent pentest evidence
```

## Health (last control — 2026-08-13, GitHub only)

- Pre-merge CI run `31706150882` on `a9cb4ed` (clean re-run): backend **315 passed · 1 skipped**; Playwright **36 passed** against real Chromium/backend/Postgres/Redis. Two independent runs produced identical counts — no flake.
- CodeQL run `31706145455`: Python, JavaScript/TypeScript and Actions analyses passed after closure security fixes.
- ruff, mypy (85 files), `alembic check` (no drift), `check_permissions`, `check_permissions_db`, `check_tenancy`, `check_no_money_floats` PASS  
- admin-web + scanner-pwa builds PASS  
- PR #55 merged at `2a1002d` on 2026-08-13 with all 14 required checks green. `main` branch protection (1 approving review, `enforce_admins`, 3 required checks, no force-push/deletion) was verified restored byte-for-byte after the merge.
- Dependabot: all 10 open alerts (vite/esbuild) are already fixed on this branch (vite 6.4.3, esbuild 0.25.12); they close when PR #49 lands  
- See `backend/docs/plans/CONTROL_HEALTH_REPORT.md`  
