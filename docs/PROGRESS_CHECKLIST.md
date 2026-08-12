# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-12  
**Program:** Phase **27 — Final Production Closure** (`backend/docs/plans/PHASE_27_FINAL_PRODUCTION_CLOSURE.md`)  
**Alembic head:** `u4b5c6d7e8f9` on branch `feat/phase27-ui-production-closure` (PR #49); `t3a4b5c6d7e8` on `main` until it merges

**Truth rules:**
- Prefer **MERGED on main** after green **required** CI over vague “done”.
- Do **not** claim **production-ready** until Phase 27 P0 closed + evidence gates + independent human APPROVE.
- MVP code on main ≠ production-ready. Phase 26 PASS is **NOT** currently verified.
- Required CI red → not CI VERIFIED / not LOCKED.

**Maturity:** IMPLEMENTED · MERGED · CI GREEN on PR #49 (`a051f52`) · PRODUCTION **NO-GO** (Phase 26 exit gate)

---

## Snapshot (honest)

| Band | Status | Note |
|------|--------|------|
| Phase 0–7 core gate | 🟢 MERGED | Architecture GO |
| Phase 8–15 domain | 🟢 MERGED | Tenancy/finance/outbox strong |
| Phase 15.5 integrity | 🟢 MERGED | Maintain |
| Phase 16–20 product MVP | 🟢 MERGED (depth partial) | Admin/Scanner polish open |
| Phase 21–24 hardening MVP | 🟢 MERGED code / CI green | CSRF narrowed; SBOM flake isolated from the gate |
| Phase 25–26 exit / prod bar | 🔴 **NOT PASSED** | Truth corrected |
| **Phase 27 production closure** | 🟢 **UI/RBAC + device hardening done** (PR #49 open) | Role-guarded portals, real portal data, device HMAC signing + nonce (ADR-044) |
| **Production-ready** | ❌ **NO** | Public launch NO-GO |

---

## Phase checklist

### Foundation & core (0–7)
- [x] Bootstrap, Docker, FastAPI, Postgres/Alembic, tenancy, auth/MFA foundation, RLS, RBAC, CI

### Domain (8–15.5) — on main
- [x] Phase 8–15 domain engines — MERGED  
- [x] Phase 15.5 integrity (no public outbox, `*:self`, event registry, outbox max-attempts) — MERGED PR #25  

### Product stack (16–20) — on main
- [x] Phase 16 Notifications & Reports API + migration `q0…` (+ console email adapter #42)  
- [x] Phase 17 `/me/*` self-service + public `POST /api/v1/auth/login|logout` (#37); 17B/C staff/OpenAPI gaps remain  
- [x] Phase 18 vertical slice E2E — service-layer **+ HTTP/ASGI** (`test_http_vertical_slice.py` #39)  
- [x] Phase 19 Admin Web — login, create member/location, **GymClubNex brand system** (#37–#38, #45)  
- [x] Phase 20 Scanner PWA — camera QR + paste, **Access brand polish** (#40, #44)  

### Hardening (21–24) — on main (MVP depth)
- [x] Phase 21 CI V2: admin-web + scanner-pwa build jobs (not yet **required** branch checks)  
- [x] Phase 22 `Dockerfile.prod` multi-stage non-root  
- [x] Phase 23 CORS (prod env) + headers + **HSTS/CSP baseline** (#41) + light login rate limit  
- [x] Phase 24 request-id / structured access logging  

### Exit (25–26)
- [x] Phase 25 checklist truth model (docs)  
- [ ] Phase 26 CORE MVP EXIT GATE — **NOT PASSED** (superseded by Phase 27 closure; independent APPROVE + green CI required)

### Phase 27 — UI production closure (RBAC portals)

Closed the gap between the "5 portals live" claim and the code. Before this wave
`/superadmin` and `/trainer` were pure mock, `/member` called a hardcoded member
id, and no portal was role-guarded (`RequireAuth` only read a localStorage
string).

- [x] `GET /api/v1/me/session` — role + permission payload for the frontend guard  
- [x] `trainer_assignments` table + RLS (migration `s2f3a4b5c6d7`) → TRAINER sees only assigned members (`members:read` endpoint scope, `members:read:all` row scope)  
- [x] `/api/v1/admin/*` federation endpoints — ADR-043: no RLS widening, per-tenant loop, 50-row page cap, `partial` flag  
- [x] `audit_events` RLS + superuser tenant impersonation written to audit (migration `t3a4b5c6d7e8`)  
- [x] Two real holes closed: `devices:manage` granted to no role (migration `r1e2f3a4b5c6`); MEMBER fallback in `authorization.py` returned True without a tenant check  
- [x] `AuthContext` + `RequireRole`, role-based post-login routing, `/portal` filtered by role  
- [x] MemberPortal → `/access/qr/issue-self`, shared api client, real membership/entitlement data, QR rendered locally (access token no longer leaves the origin)  
- [x] TrainerPortal + SuperAdminPortal wired to real APIs, invented KPIs deleted  
- [x] PWA icon set produced for both apps — manifests previously pointed at files that did not exist (admin-web) or flat placeholder squares off-theme (scanner-pwa); `any` + `maskable` purposes split, `theme_color` aligned to `#020617`  
- [x] CSRF `Authorization: Bearer` exemption narrowed to requests with no `session_token` cookie (an attacker-supplied header no longer waives the check) + regression test  
- [x] Docs: `docs/ARCHITECTURE.md` (moved into the repo, verified against code), `docs/RBAC.md`, ADR-043  

**Evidence (local, 2026-08-12):** backend `pytest` 299 passed · 1 skipped; Playwright e2e 21 passed against real Chromium + real backend (QR issue→validate→replay 409 round trip included); zero console errors across all 5 portals (`console_clean.spec.ts`); ruff, mypy, `check_permissions`, `check_permissions_db`, `check_tenancy`, `check_no_money_floats`, both frontend builds green.

**Known gaps (not closed, deliberately):**
- No external pentest; the ASVS L2 report is **SELF-ASSESSED**, not verified.

## Phase 27.1 — Device channel hardening + CodeQL closure (2026-08-12)

- [x] Device requests require HMAC-SHA256 signing: per-session secret issued once by `POST /devices/auth` (body, never a cookie), `X-Device-Signature` over `METHOD\npath\ntimestamp\nnonce\nsha256(body)`, ±300s skew, single-use nonce in `device_nonces` (new table, RLS on, migration `u4b5c6d7e8f9`). A stolen `device_session` cookie is no longer a credential on its own; pre-signing sessions fail closed with `device_session_unsigned`.
- [x] `get_current_device` now establishes tenant context from the bootstrap session row *before* reading `devices`, so the devices table is no longer read outside RLS (it previously depended on the connection role not enforcing it).
- [x] scanner-pwa signs device requests via Web Crypto. `authenticateDevice()` imports the secret into a **non-extractable** `CryptoKey` and persists only that handle in IndexedDB — the plaintext never reaches a storage API, so script on the origin can sign but cannot exfiltrate the credential (keeps ASVS 3.4.2 true). Falls back to the staff `/access/qr/validate` path when unpaired.
- [x] CodeQL: cleared the high alert (demo seed script no longer echoes the password) and the 5 `actions/missing-workflow-permissions` alerts (top-level `permissions: contents: read` in `ci.yml`).

- [x] CI hardening: SBOM generation split out of the `security` gate (an upstream syft/GitHub-releases outage was failing `security` and, through `needs`, skipping the whole test suite), `anchore/sbom-action` pinned to a SHA, `timeout-minutes` on every job.

**Evidence (local + CI on `630aeef`, 2026-08-12):** backend `pytest` **301 passed · 1 skipped** (local and CI), Playwright e2e **21 passed** against real Chromium + real backend with zero console errors, all 12 CI checks green including CodeQL. `tests/api/test_scanner_device_auth.py` 3 passed — cookie-only, forged signature, body/signature mismatch, stale timestamp, nonce replay, and unsigned-session paths each asserted 401 with their distinct reason; ruff, mypy (85 files), `alembic check` (no drift), `check_tenancy`, `check_permissions*`, `check_no_money_floats`, all three frontend builds green.

---

## Closed on main (feature waves)

| Wave | PRs | Highlights |
|------|-----|------------|
| Integrity | #25 | Phase 15.5 |
| Product stack | #26 | Phases 16–26 docs + MVP code stack |
| Remaining MVP | #37–#42 | Auth login, seed, admin CRUD basics, camera QR, HTTP e2e, HSTS/CSP, console email |
| UI brand | #44–#45 | Scanner Access brand + Admin teal brand system |
| Docs | #43 | Board / checklist SHA truth |
| Prod Hardening | #48 | Strict HttpOnly Cookies, Pytest Deadlock Fix, Full Mypy/Ruff compliance, Test isolation |

---

## Remaining to “complete” production bar

1. ~~Real notification transports (SMTP/SMS/WhatsApp) behind adapters~~ (SMTP completed, others deferred)
2. ~~Admin cookie-only session (drop localStorage token) + day-1 ops UI (edit, membership lifecycle, finance)~~ (Completed)
3. ~~Scanner device auth / offline~~; FE builds as **required** checks (Completed)
4. ~~Observability productization (health deps, metrics/traces/alerts)~~ (Completed `/live`, `/ready`, `/health`)
5. ~~Backup/restore script & ASVS L2 compliance report~~ (Completed)

Live backlog: `backend/docs/plans/REMAINING_WORK_BOARD.md`

---

## Related docs

- `docs/REVIEW_CHECKPOINT.md`  
- `docs/IMPLEMENTATION_MASTER_PLAN.md`  
- `backend/docs/plans/phase26_core_mvp_exit_gate.md`  
- `backend/docs/plans/CONTROL_HEALTH_REPORT.md`  
- `backend/docs/plans/REMAINING_WORK_BOARD.md`  
- `backend/docs/plans/STANDING_REVIEW_latest.md`  
- `frontend/UI_BRAND_SYSTEM.md`  
- `READY_TO_RUN.md`  
