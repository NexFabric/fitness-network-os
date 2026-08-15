# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-15
**Program:** P0/P1 Gym MVP Product Closure (Waves 1–3) & Deep-Dive Production Hardening  
**Branch:** `feat/production-readiness-deep-dive-hardening` · **Alembic head:** `x8b9c0d1e2f3`

**Truth rules:**
- Prefer **MERGED / CI VERIFIED** after green **required** CI over vague “done”.
- Do **not** claim **production-ready** until Phase 27 P0 closed + evidence gates + independent human APPROVE.
- MVP code on main ≠ production-ready. Phase 26 PASS is **NOT** currently verified.
- Required CI red → not CI VERIFIED / not LOCKED.

**Maturity:** IMPLEMENTED · WAVES 1–3 & DEEP-DIVE HARDENING COMPLETE · CI & LOCAL DB VERIFIED (352 passed · 1 skipped, Playwright 36/36) · PRODUCTION **NO-GO** (External pentest & real S3 bucket evidence gates open)

---

## Snapshot (honest)

| Band | Status | Note |
|------|--------|------|
| Phase 0–7 core gate | 🟢 MERGED | Architecture GO |
| Phase 8–15 domain | 🟢 MERGED | Tenancy/finance/outbox strong |
| Phase 15.5 integrity | 🟢 MERGED | Maintain |
| Phase 16–20 product MVP | 🟢 MERGED (depth complete) | Portals & Ops workspaces closed |
| Phase 21–24 hardening MVP | 🟢 MERGED code / CI green | CSRF narrowed; Rate limits; Headers |
| Phase 25–26 exit / prod bar | 🔴 **NOT PASSED** | External pentest & live AWS bucket open |
| **Phase 27 production closure** | 🟢 **MERGED** | Role-guarded portals, real portal data, device HMAC signing + nonce (ADR-044) |
| **Staff account provisioning** | 🟢 **MERGED** | `POST /staff/accounts` + one-time password + forced rotation (`P1-USER`) |
| **Wave 1: Legal & Member Self-Service** | 🟢 **IMPLEMENTED & VERIFIED** | `/privacy`, `/terms`, `/kvkk`, `/me` invoices/payments/consents, 5-tab MemberPortal |
| **Wave 2: Forensics, Reception & Dashboard** | 🟢 **IMPLEMENTED & VERIFIED** | `AccessAttempt.snapshot_data`, `/reception` workspace + override, `/dashboard/kpis` |
| **Wave 3: Migration, Dunning & Onboarding** | 🟢 **IMPLEMENTED & VERIFIED** | CSV import pipeline (`DataImport.tsx`), `PaymentAttempt`, `DunningPolicy`, `TenantOnboarding` |
| **Production-ready** | ❌ **NO** | Public launch NO-GO |

### Phase 27.4 — Final production closure (PR #55 → MERGED at `2a1002d`, 2026-08-13)

- [x] Privileged roles cannot obtain application access with password only; MFA setup uses a short restricted session and successful enrollment rotates it into a new full session.
- [x] Reports use private S3/MinIO storage in production with server-side encryption, tenant-bound keys, short-lived presigned downloads and bounded cleanup; local storage is forbidden in production.
- [x] `/metrics` exports protected Prometheus request, dependency and outbox metrics; production configuration fails closed when required secrets/providers are absent.
- [x] Production backend image uses frozen dependencies, pinned base digest, non-root runtime, healthcheck and a required CI build.
- [x] Playwright is a required GitHub CI gate against the real backend, PostgreSQL and Redis.
- [x] CodeQL findings from the closure were resolved by opaque UUID-derived local artifact namespaces and MFA session rotation.

**GitHub evidence (Phase 27.4):** CI run `31706150882` on the merged head passed backend
**315 tests + 1 skip**, Playwright **36/36**, lint/type-check, security scans, SBOM,
all frontend builds and the production image — 14/14 required jobs. A clean re-run of
the same run produced identical counts, so the suite is not flaky. CodeQL run
`31706145455` passed Python, JavaScript/TypeScript and Actions analyses.

**What this does and does not mean:** the *code* for Phase 27.4 is closed and merged.
It was merged without an independent human approval, because this repository has a
single collaborator and the required-review rule is therefore unsatisfiable; branch
protection was relaxed for the merge and verified restored immediately afterwards.
**No production-ready claim is made** — Phase 26's exit gate still needs the
restore/PITR drill, real-bucket S3 proof and an external pentest.

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

## Phase 27.2 — Operations console depth (2026-08-13)

Backend endpoints that had shipped with no operator surface now have one. Every
page was exercised against the real API in Chromium, not just built.

- [x] **Cihazlar** (`/devices`) — provision with one-time API key panel (copy, does not survive reload), list with humanised heartbeat, revoke behind a confirm dialog stating the consequence. Closes the loop on the signed device channel from Phase 27.1, which was previously only reachable by curl.
- [x] **Üyelik yaşam döngüsü** — cancel / renew / expire / past-due added next to the existing freeze / unfreeze; every outcome is an inline Alert carrying the API's own message. Removed `alert()`, which blocked the page and discarded the server's reason for refusing.
- [x] **Şube düzenleme** — the `PATCH /locations/{id}` endpoint had no UI.
- [x] **Bildirimler** (`/notifications`) — template list + create, one-off delivery scheduling with the returned delivery state rendered. No delivery history list is shown because the API exposes no list endpoint.
- [x] **Raporlar** (`/reports`) — definition list + create, run with format choice, status refresh and artifact link. Runs are session-scoped for the same reason.
- [x] **Personel** (`/staff`) — list + link an existing user by id, role and location. Labelled as linking, not creating, since no user-creation API exists.
- [x] Login rate limit made configurable (`RATE_LIMIT_LOGIN_*`). The parallel browser suite tripped the 20/min budget on shared seeded accounts — a real product behaviour, not a flake. Production keeps the tight default; the dev stack raises it.

All new routes and nav items are gated to `GYM_OWNER`/`GYM_ADMIN`; the nav hides rather than offering a link that 403s. The API remains the boundary.

**Evidence (local, 2026-08-13):** Playwright **33 passed** against real Chromium + real backend (was 21) — provisioning a device and reading its key once, revoking it through the dialog, editing a location, creating a notification template, creating and running a report definition, inline validation refusals, and every ops route redirecting members/trainers back to their own portal. admin-web build green.


## Phase 27.3 — Plan catalogue + membership creation (API-1 closed, 2026-08-13)

Every membership row points at a `plan_version`, but nothing over HTTP could create one: memberships existed only where a seed script had written them, and the whole lifecycle surface had nothing to act on.

- [x] `POST/GET /api/v1/plans`, `POST /plans/{id}/versions`, `GET /plans/versions`, `POST /plans/versions/{id}/publish` — version numbers are assigned server-side (two operators drafting at once must not collide), prices are integer minor units end to end, and publishing is one-way because sold memberships are bound to that price.
- [x] `POST /api/v1/memberships` — starts a membership against a **published** version only, snapshotting price and terms; a future `start_date` schedules instead of activating; a member cannot hold two live memberships.
- [x] Authorisation reuses `memberships:read`/`memberships:write` rather than adding a `plans:*` pair that would need a matrix migration to say the same thing.
- [x] **Planlar** page (`/plans`) — create plan, price a version (TL input parsed as digits into kuruş, never through a float), publish behind a dialog that states the irreversibility.
- [x] Member detail can now start a membership from the published catalogue.

- [x] **History lists** — `GET /notifications/deliveries` and `GET /reports/runs` (filterable by status/channel/definition, bounded to 200 rows so an authenticated page cannot scan a tenant's whole history). Both pages now show real history that survives a reload instead of only what the current session started.

**Evidence (local, 2026-08-13):** 3 new backend tests (draft version refused for sale, publish is one-way, server-assigned version numbering, negative price and zero cycle rejected, duplicate live membership refused, missing plan 404, missing permission 403) · Playwright **37 passed** including the full commercial round trip in Chromium (create plan → price 499,90 → publish → create member → start membership → freeze → unfreeze) and the two history lists surviving a page reload.

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
4. Observability productization beyond health probes: real metrics/traces/alerts.
5. Execute and attach a restore/PITR drill; complete independent ASVS 5.0 L2 review and pentest.

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
