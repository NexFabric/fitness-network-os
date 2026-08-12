# Phase 27 — Final Production Closure

**Date:** 2026-08-10  
**Status:** ACTIVE program (replaces premature Phase 26 PASS claims)  
**Rule:** No new feature waves until P0 is green. Architecture redesign is **out of scope**.  
**Source audit:** Independent deep-dive on main (CI red, CSRF/auth, truth drift, scanner, reports, etc.)

---

## Final hüküm (locked for this phase)

| Area | Verdict |
|------|---------|
| Architecture / tenancy / finance / outbox / QR core | 🟢 GO — **do not redesign** |
| Admin / Scanner product depth | 🟡 |
| Auth session (browser contract) | 🔴 P0 |
| CSRF (real browser + real tests) | 🔴 P0 |
| CI required suite on main | 🔴 P0 |
| Reports artifact | 🔴 P1 |
| MFA privileged | 🔴 P1 |
| Production evidence (DR/pentest) | 🔴 unverified |
| Public production launch | 🔴 **NO-GO** until P0+critical P1 closed |

**Target chain:**
```text
main GREEN → security verified → production gates → independent APPROVE → PUBLIC GO
```

---

## Agent roster

| Agent ID | Role | Owns | Stack |
|----------|------|------|-------|
| **A-CI** | CI Stabilizer | Pytest green, event-loop, flaky isolation | backend/tests, CI workflows |
| **A-AUTH** | Browser Auth & CSRF | Cookie-only admin, CSRF bootstrap, E2E login | backend auth/csrf, admin-web |
| **A-TRUTH** | Docs Truth | Checklist/board/ready-to-run consistency | docs/*, plans/* |
| **A-SCAN** | Scanner Production | Device auth, offline policy, no staff token paste | scanner-pwa, access API |
| **A-RPT** | Reports Real | Artifact storage, signed URL, no fake SUCCEEDED | report service |
| **A-NTF** | Notifications Hardening | PII logs, fail-closed prod providers | notification adapters |
| **A-MFA** | Privileged MFA | Enrollment/challenge/step-up for privileged roles | auth + MFA models |
| **A-CFG** | Production Config | Fail-closed boot, TrustedHost, CORS, cookies | config, main.py |
| **A-OBS** | Observability | /live /ready metrics baseline | health, logging |
| **A-FE** | Frontend Quality | Public CI, Vitest/RTL, Playwright smoke | all frontends |
| **A-OPS** | Ops Evidence | DR drill, SBOM pins, container freeze | Docker, runbooks |
| **A-QR** | Key Custody | KMS/Vault resolver (after P0) | qr_crypto |
| **ORCH** | Orchestrator | Merge order, no parallel conflict on same files | human + lead agent |

---

## Dependency DAG (merge order)

```text
Wave 0 (parallel, docs-only)     A-TRUTH
        │
Wave 1 (serial or careful PR)    A-CI  ──must green──►  gate
        │
Wave 2 (auth stack, one PR preferred)
        A-AUTH (CSRF bootstrap + cookie-only admin + real E2E)
        │
Wave 3 (parallel product P1)
        A-SCAN │ A-RPT │ A-NTF │ A-CFG │ A-FE
        │
Wave 4 (security depth)
        A-MFA │ A-OBS │ A-QR
        │
Wave 5 (evidence)
        A-OPS + independent human APPROVE
```

**Conflict zones (never two agents same time):**
- `backend/app/api/middleware/csrf.py` + `deps.py` + `security.py` → **A-AUTH only**
- `docs/PROGRESS_CHECKLIST.md` / `PRODUCTION_READINESS.md` → **A-TRUTH only** after each wave
- `frontend/admin-web/src/api/client.ts` → **A-AUTH** then **A-FE**

---

# P0 — Release blockers (Wave 0–2)

## P0-1 · Current main pytest GREEN
| Field | Value |
|-------|--------|
| **Agent** | **A-CI** |
| **Priority** | P0 |
| **Evidence now** | GitHub CI on main `506fb95` / recent: Unit & Integration Tests **FAILURE**; annotations: exit 1, `Event loop is closed` |
| **Work** | Reproduce locally; fix async fixture/event-loop closed; CSRF-test interaction; no silent skip of security tests without replacement |
| **Acceptance** | Required check **Unit & Integration Tests** green on `main`; Security Scans + Lint green; no permanent CSRF off in prod code paths |
| **DoD** | `gh run list --branch main` latest CI success; PR description lists root cause |
| **Files** | `backend/tests/**`, `backend/tests/conftest.py`, possibly CSRF middleware only if tests need real double-submit fixture |

## P0-2 · Real CSRF bootstrap + production-like E2E
| Field | Value |
|-------|--------|
| **Agent** | **A-AUTH** |
| **Priority** | P0 |
| **Evidence** | Cookie written only after `call_next`; non-exempt POSTs need header; `ENVIRONMENT=test` full bypass means tests don’t prove browser CSRF |
| **Nuance** | Login/logout currently in `EXEMPT_PATHS` — bootstrap still required for **member create / other POSTs** and if exemptions are removed later |
| **Work** | Prefer `GET /api/v1/auth/csrf` (or any safe bootstrap) that sets `csrf_token` cookie **before** unsafe calls; admin client always loads CSRF then sends `X-CSRF-Token`; HTTP E2E: bootstrap → login → create member → 403 without token |
| **Acceptance** | Fresh browser: login + create member works; missing CSRF → 403; tests use real middleware (not total bypass) or dedicated CSRF suite with double-submit |
| **Files** | `csrf.py`, `auth.py`, `admin-web/src/api/client.ts`, `test_http_vertical_slice.py` / new `test_csrf_browser.py` |

## P0-3 · Admin cookie-only session (no browser raw token)
| Field | Value |
|-------|--------|
| **Agent** | **A-AUTH** |
| **Priority** | P0 |
| **Evidence** | Spec: HttpOnly cookie session; admin must not store session secrets in JS-readable storage |
| **Current** | `setAuth(tenantId)` only (good direction); comments still say Bearer/localStorage token; backend may still return raw token / Bearer fallback outside test |
| **Work** | Login JSON: **no raw session token** to browser; cookie `Secure` in production; admin: only tenant id (or fetch tenant from `/me` after cookie login); Bearer only for non-browser clients (curl/CI) via explicit non-browser contract; 401 → clear + login |
| **Acceptance** | DevTools Application: no session secret in localStorage; Network: cookie sent; members list 200 after login |
| **Files** | `auth.py`, `deps.py`, `security.py`, `admin-web` Login + client + RequireAuth |

## P0-4 · Phase 26 / truth docs match reality
| Field | Value |
|-------|--------|
| **Agent** | **A-TRUTH** |
| **Priority** | P0 |
| **Evidence** | Checklist YES vs STANDING_REVIEW NO vs READY_TO_RUN head/tail contradiction |
| **Work** | Single truth: Production-ready **NO** until Phase 27 gates pass; Phase 26 = **NOT PASSED / SUPERSEDED by 27**; align PROGRESS_CHECKLIST, REMAINING_WORK_BOARD, PRODUCTION_READINESS, READY_TO_RUN, phase26 doc banner |
| **Acceptance** | Zero internal contradictions on “production-ready” and Phase 26; board lists open P0–P2 honestly |
| **Files** | `docs/PROGRESS_CHECKLIST.md`, `docs/PRODUCTION_READINESS.md`, `READY_TO_RUN.md`, `backend/docs/plans/*` |

---

# P1 — Before public launch (Wave 3–4)

## P1-1 · Scanner device authentication
| **Agent** | **A-SCAN** |
| **Work** | Device credential (not staff session paste); bind location/tenant; rotate; audit log |
| **Acceptance** | No `fnos_scanner_token` staff secret paste UX as primary path; validate requires device identity |

## P1-2 · Scanner offline policy
| **Agent** | **A-SCAN** |
| **Work** | Define offline: deny-by-default OR signed offline grant with TTL; document; no fake “offline PASS” |
| **Acceptance** | Policy written + implemented + tested; UI matches behavior |

## P1-3 · Report real artifact
| **Agent** | **A-RPT** |
| **Work** | Real query → bytes → private storage → encryption → signed URL → expiry → cleanup; never SUCCEEDED with empty fake URL |
| **Acceptance** | Downloadable artifact; tenancy isolation tests; remove `memory://` success path |

## P1-4 · Privileged MFA enforcement
| **Agent** | **A-MFA** |
| **Work** | Enroll/challenge/verify for PLATFORM_SUPER_ADMIN, FEDERATION_ADMIN, GYM_OWNER, SUPPORT_PRIVILEGED; login step-up |
| **Acceptance** | Privileged login blocked without MFA; model wired to endpoints |

## P1-5 · Production config fail-closed
| **Agent** | **A-CFG** |
| **Work** | production boot fails if CORS_ORIGINS empty, ALLOWED_HOSTS empty, insecure cookie flags, dangerous notification defaults |
| **Acceptance** | Unit tests for boot fail; docs list required env |

## P1-6 · Notification PII + provider semantics
| **Agent** | **A-NTF** |
| **Work** | No `recipient_address=` in logs; SMS/WA/PUSH not silent success-as-log in prod; SMTP remains; fail-closed misconfig |
| **Acceptance** | Log scrub tests; prod env refuses log-only as “success transport” for email if configured for real delivery |

## P1-7 · Frontend browser E2E
| **Agent** | **A-FE** |
| **Work** | Playwright: login, member create/edit, membership, finance view, QR validate, logout/session expiry |
| **Acceptance** | CI job green (can be non-required first, then required) |

## P1-8 · Public-site CI job
| **Agent** | **A-FE** |
| **Work** | `npm run build` (+ lint) for public-site in CI |
| **Acceptance** | Job on PR/main |

## P1-9 · Hardcoded / fake marketing metrics
| **Agent** | **A-FE** (+ backend if endpoint exists) |
| **Work** | Remove “Kanıtlanmış Performans / sayılar yalan söylemez” with fake 99.99%; use “tasarım hedefleri” or hide until real telemetry |
| **Acceptance** | No false production claims on live marketing |

## P1-10 · DR / restore evidence
| **Agent** | **A-OPS** |
| **Work** | Documented restore drill, RPO/RTO measurement, or explicit “unverified” gate |
| **Acceptance** | Evidence file under `docs/ops/` or NO-GO remains |

## P1-11 · ASVS / pentest evidence
| **Agent** | **A-OPS** + human |
| **Work** | External or internal ASVS L2 checklist + pentest report link; independent APPROVE |
| **Acceptance** | Signed off or gate stays NO-GO |

## P1-12 · Branch protection: FE builds required
| **Agent** | **ORCH** / DevOps |
| **Work** | Admin + Scanner (+ Public) build required after green |
| **Acceptance** | GitHub ruleset shows required checks |

---

# P2 — Hardening (Wave 4–5)

| ID | Item | Agent | Notes |
|----|------|-------|-------|
| P2-1 | `/live` + `/ready` + metrics/alerts | A-OBS | Ready fails when DB/Redis down |
| P2-2 | Distributed rate limiter (Redis) | A-CFG | Replace in-memory deque |
| P2-3 | KMS/Vault QR key resolver | A-QR | Beyond `local:hmac:` |
| P2-4 | Container digest pin + frozen uv.lock + HEALTHCHECK | A-OPS | Dockerfile.prod |
| P2-5 | Prod compose / secrets injection | A-OPS | Not dev bind-mount stack |
| P2-6 | Formal threat models | A-OPS | C9 |
| P2-7 | Staff API gaps 17B for day-1 admin | A-AUTH/FE | Only if product needs |

---

# P3 — Hygiene

| ID | Item | Agent |
|----|------|-------|
| P3-1 | Gitlink/submodule `.gitmodules` | A-CI / ORCH |
| P3-2 | GitHub Actions Node 20 deprecation | A-CI |
| P3-3 | Dead comments “Bearer localStorage” in admin | A-AUTH |

---

## Explicit non-work

- No Kafka / K8s / microservices without ADR  
- No redesign of RLS/tenancy/finance money model  
- No Membership → WhatsApp shortcut  
- No float money  
- No claiming Phase 26 PASS without independent human APPROVE + green CI + closed P0  

---

## Suggested first agent prompts (copy-paste)

### A-CI
```text
Phase 27 P0-1: Make main Unit & Integration Tests green.
Reproduce Event loop is closed / exit 1 on backend pytest.
Do not permanently disable CSRF for all tests without a real double-submit fixture path.
PR only test/CI fixes; no feature work.
```

### A-AUTH
```text
Phase 27 P0-2 + P0-3: CSRF bootstrap (GET /auth/csrf or equivalent) + admin cookie-only session.
No raw session token in browser localStorage. Secure cookie in production.
HTTP E2E: bootstrap → login → create member; 403 without CSRF on non-exempt POST.
Coordinate with A-CI so tests prove real CSRF.
```

### A-TRUTH
```text
Phase 27 P0-4: Align all truth docs — production-ready NO until Phase 27 gates.
Remove contradictions in PROGRESS_CHECKLIST, READY_TO_RUN, REMAINING_WORK_BOARD, PRODUCTION_READINESS, phase26 docs.
Point Phase 26 as NOT PASSED; Phase 27 active.
```

### A-SCAN (after Wave 2)
```text
Phase 27 P1-1/1-2: Device auth for QR validate; honest offline policy. Remove staff token paste as primary UX.
```

### A-RPT
```text
Phase 27 P1-3: Replace MVP memory:// report SUCCEEDED with real artifact pipeline or status FAILED/PENDING until storage ready.
```

---

## Progress tracking

| Wave | Agents | Exit gate |
|------|--------|-----------|
| 0 | A-TRUTH | Docs consistent NO-GO |
| 1 | A-CI | main CI green |
| 2 | A-AUTH | Cookie admin + CSRF E2E |
| 3 | A-SCAN, A-RPT, A-NTF, A-CFG, A-FE | P1 public-blockers closed or explicitly deferred |
| 4 | A-MFA, A-OBS, A-QR | Security depth |
| 5 | A-OPS + human | Evidence + APPROVE → PUBLIC GO reconsideration |

**Update this file + `REMAINING_WORK_BOARD.md` after each wave.**
