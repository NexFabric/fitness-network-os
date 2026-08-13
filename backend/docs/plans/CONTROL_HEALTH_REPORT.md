# Control Health Report — 2026-08-13 (post Phase 27.2 ops depth + 27.3 plan catalogue)

## Overall: **HEALTHY_MVP**

| Check | Result |
|-------|--------|
| Local `main` == `origin/main` | **YES** at `8b2904e` |
| Open PRs | **0** |
| Branch protection reviews | **1** required, `enforce_admins` on |
| Alembic head | `u4b5c6d7e8f9` |
| `GET /health` | **200** (when stack up) |
| Admin `:5173` / Scanner `:5174` | Runnable (Vite host) |
| Full local pytest | **311 passed · 1 skipped** (2026-08-13) |

## Merged waves (truth)

| Wave | PRs | Note |
|------|-----|------|
| 15.5 integrity | #25 | `125a8c6` lineage |
| Product stack | #26 | Phases 16–24 MVP |
| Remaining MVP | #37–#42 | Auth, CRUD create, camera, e2e, HSTS, console email |
| UI brand | #44–#45 | Scanner Access + Admin teal brand |
| Docs | #43 + docs truth pass | SHA / checklist aligned |
| Phase 27 + 27.1 | **#49 merged** | RBAC portals, PWA icons, CSRF narrowing, device HMAC signing (ADR-044) |
| Phase 27.2 + 27.3 | **#52 merged, 27.3 in PR** | Ops console depth, plan catalogue + membership creation, history endpoints |

## Phase matrix

| Phase | On main | Depth |
|-------|---------|--------|
| 0–15.5 | YES | Full integrity for 15.5 |
| 16–20 | YES | Product MVP + brand |
| 21–24 | YES | Hardening MVP / not LOCKED |
| 25–26 | YES docs | Exit **NOT PASSED** |
| 27–27.1 | YES | Merged via #49 (`8b2904e`) |

## Security posture (2026-08-12)

- Device channel: HMAC-SHA256 request signing + single-use nonce; a stolen
  `device_session` cookie is not a usable credential (ADR-044).
- Scanner holds its signing key as a non-extractable `CryptoKey` (IndexedDB) —
  no plaintext secret in web storage.
- CodeQL: green. One alert dismissed with reasoning
  (`py/weak-sensitive-data-hashing` on `_hash_api_key`: 256-bit server-minted
  token, not a human password).
- Dependabot: **0 open alerts** — the 10 vite/esbuild alerts closed when #49 landed
  (vite 6.4.3, esbuild 0.25.12).
- Former CI flake fixed: `anchore/sbom-action` (transient syft download failures)
  now runs in its own `sbom` job, so it can no longer skip the test suite.

## Production-ready?

**NO.** Remaining: real providers, day-1 ops UI depth, observability,
backup/restore drill evidence, external pentest, Phase 26 PASS.

## Safe to continue?

**YES** for main development and local demo. Do not market as production until
Phase 26 PASS.

## Backlog

- `docs/PROGRESS_CHECKLIST.md`
- `backend/docs/plans/REMAINING_WORK_BOARD.md`
