# Tech Debt Register

Items that are real work, not bumps. Each one was found by something concrete
(a failing gate, a rejected dependency PR) — not by speculation. Add a row only
with the evidence that produced it.

| ID | Item | Found by | Size | Notes |
|----|------|----------|------|-------|
| TD-2 | `react-dom` major upgrade | Dependabot PR #73 (closed 2026-08-16) | M | Breaks Admin Web Build and Frontend Images. A React major deserves a dedicated branch with a full Playwright pass, not a dependency bump. |
| TD-3 | Runtime majors are build-tested only | Dependabot PRs #63/#67/#69 (closed 2026-08-16) | S | `ci.yml` pins `python-version: "3.12"` and installs node via `setup-node`, so a base-image major bump only proves the image builds. `dependabot.yml` now ignores python/node majors. Raising a runtime means moving the CI matrix in the same PR. |
| ~~TD-5~~ | `eslint` 9 → 10 (with `@eslint/js` 10) | Dependabot PR #71 → superseded by #84 | — | **Resolved by PR #84**, which does what #71 could not: it moves the eslint core to 10.8.1 so `@eslint/js@10`'s `peerOptional eslint@^10` actually resolves. Kept here because the diagnosis is the reusable lesson — a peer-pinned plugin bump is never a standalone update. |
| TD-6 | `@vitejs/plugin-react` 4 → 6 | Dependabot PR #82 (closed 2026-08-16) | S | Breaks all three frontend builds on its own. It tracks the Vite major — move the two together, never separately. |
| TD-7 | `tailwindcss` 3 → 4 | Dependabot PR #85 (closed 2026-08-16) | M | Breaks all three frontend builds. Tailwind 4 changes the config format and the CSS entry point; this is a migration with a visual review, not a version bump. |

## Closed

| ID | Item | Closed by |
|----|------|-----------|
| TD-0 | Dev `backend/Dockerfile` could not build — unpinned `uv` drifted past the `uv_build<0.12.0` bound and the local package was built at a layer without `src/` | 2026-08-16, aligned with `Dockerfile.prod` (`uv==0.11.21` + `--no-emit-project`) |
| TD-1 | `eslint-plugin-react-hooks` 5 → 7 (12+ render/setState useEffect smells across admin-web & scanner-pwa) | 2026-08-16, refactored all impure state updaters, sync setStates in effects, and hook dependency loops |
| TD-4 | No CI job runs the ops drills | 2026-08-16, added `.github/workflows/ops-drills.yml` with scheduled weekly Sunday run + workflow_dispatch |
