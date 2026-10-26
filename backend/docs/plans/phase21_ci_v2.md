# Phase 21 — CI V2 Full Verification (Frontend Jobs)

**Status:** 🟠 **IMPLEMENTED on branch** — **not LOCKED**  
**Branch:** `feat/phase16-notifications-reports` (PR #26 mega branch)  
**Workflow:** `.github/workflows/ci.yml`  
**Do not claim:** production-ready / full CI V2 complete

---

## Goals

1. **Keep** existing backend gates unchanged:
   - `security` — Bandit + pip-audit + TruffleHog (Safety CLI removed — it no longer boots; pip-audit is the SCA gate). CodeQL is a separate required job.  
   - `lint` — ruff, mypy, tenancy static, permissions matrix, no-money-floats  
   - `test` — migrations, schema drift, dynamic tenancy, permissions DB parity, pytest  
2. **Add** frontend production-build jobs so Phase 19 (admin-web) and Phase 20 (scanner-pwa) cannot merge broken TypeScript/Vite output.  
3. Prefer **parallel, independent** frontend jobs (no `needs:` on backend) so UI builds fail fast without waiting for Postgres pytest.  
4. Preserve monorepo install truth: npm **workspaces** live under `frontend/` with a single root lockfile.

---

## What landed

| Job id | Display name | What it does |
|--------|--------------|--------------|
| `admin-web` | Admin Web Build | Node **20**, `npm ci` at `frontend/`, `npm run build` in `frontend/admin-web` |
| `scanner-pwa` | Scanner PWA Build | Node **20**, `npm ci` at `frontend/`, `npm run build` in `frontend/scanner-pwa` |

### Install / build notes

- **Lockfile path:** `frontend/package-lock.json` (workspaces: `admin-web`, `scanner-pwa`, `packages/*`).  
- Per-app directories do **not** have their own lockfiles, so `npm ci` runs at **`./frontend`**, then build uses `working-directory` for each app (matches task intent: Node 20 + ci + build for each package).  
- `cache-dependency-path: frontend/package-lock.json` for setup-node npm cache.  
- `VITE_API_URL=http://localhost:8000` set at build time so Vite embeds a non-empty API base (same default as local README).  
- **No path filters** were present on this workflow; none were added (full CI still runs on push/PR to `main`).

### Explicit non-goals (this phase slice)

- Not required: frontend unit/e2e tests, ESLint job (admin/scanner lint scripts reference eslint without a dependency).  
- Not required: Docker image build/push for frontends (Dockerfiles exist; container hardening is Phase 22).  
- Not required: making frontend jobs required branch-protection checks (ops/GitHub settings).  
- Not LOCKED until green on the target branch and progress docs say so.

---

## CI topology (after this change)

```
push / PR → main
├── security          (backend)
├── lint              (backend)
├── test              (needs: security, lint; postgres + redis)
├── admin-web         (frontend workspace build)
└── scanner-pwa       (frontend workspace build)
```

Backend jobs are unchanged; frontend jobs are additive only.

---

## Verify locally

```bash
cd frontend
npm ci
(cd admin-web && VITE_API_URL=http://localhost:8000 npm run build)
(cd scanner-pwa && VITE_API_URL=http://localhost:8000 npm run build)
```

Or workspace-scoped:

```bash
cd frontend && npm ci
npm run build -w admin-web
npm run build -w scanner-pwa
```

Validate workflow YAML (example):

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```

---

## Next (related track)

- Phase 22: production container hardening  
- Phase 23: HTTP security baseline (CORS allowlist, security headers)  
- Optionally: path filters later if CI cost becomes an issue (do not weaken security/lint/test gates)  
- Optionally: `npm audit` / Dependabot for frontend workspaces  

---

## References

- Phase 19 plan: `backend/docs/plans/phase19_admin_web.md`  
- Phase 20 plan: `backend/docs/plans/phase20_scanner_pwa.md`  
- Master plan: `docs/IMPLEMENTATION_MASTER_PLAN.md` (Phase 21+)  
- Progress: `docs/PROGRESS_CHECKLIST.md`  
