# Campaign register — do not redo closed work

**Date:** 2026-08-16  
**Authority:** `docs/PROGRESS_CHECKLIST.md`  
**Pickup:** `docs/HANDOFF.md`  
**Last code on `main`:** `1b42ab4`  
**Alembic head:** `xi0d1e2f3a4b`  
**Production-ready?** **NO**  
**Phase 26 PASS?** **NO / NOT VERIFIED**

This file exists so the next agent does **not** re-implement, re-PR, or
re-review work that already landed. Read this before opening a new
certification, TLS, coverage, a11y, migrate, or ops-drills branch.

---

## Closed on `main` — do not re-implement

| ID / PR | SHA | What landed | Do not |
|---|---|---|---|
| **#89** certification | `e05e29f` | migrate-before-app, migrator-only DSN, TLS / `PRODUCTION_PRIVATE_NETWORK`, ops-drills PITR, coverage floors, Safety CLI dropped (pip-audit is SCA), EXTERNAL_GATES packets | rewrite compose, re-add Safety, invent a second migrate gate |
| **#91** truth headers | `27fff12` | authority docs mark #89 MERGED | reopen an “#89 is OPEN” story |
| **#93** release-truth | `d9a5c9d` | `backend/scripts/check_release_truth.py` forbids stale OPEN vs MERGED pairs | rewrite the checker; do not claim #89 OPEN |
| **2026-08-21** audit hardening | `HEAD` | federation revenue status bug fix (`SUCCEEDED`), root `ErrorBoundary`, reception N+1 batch query, `/me` pagination caps, import plan cache, modal a11y dialog roles, Dashboard error retry | re-open federation CAPTURED bug or N+1 query loop |
| **#94** TLS proof | `1b42ab4` | host `chown 999:999` of TLS proof certs; encrypt-only SSL context | `docker exec chown` on a dead container; re-break verify-full |
| **#62** Phase 29 + RC | `ae6267d` | BOLA, MFA/step-up/idle, `fernet:hmac:`, portal bind, DSAR, PT EXCLUDE, … | reopen Phase 29 product work |
| **#78** local drills | `fb3a26d` | S3 10/10 MinIO, dump/restore + PITR, observability drill | re-run as if never executed; local ≠ AWS |
| **#80** deps + HAND-1 record | `d56b6a0` | dependency batch, HAND-1 template, dependabot scope | re-batch the same deps |
| **#83 / #84** | `ee6597e` / `1d5999b` | vite 8.2.1, eslint 10.8.1 | reopen those bumps |
| **#64 / #66 / #68** | — | CI action bumps | duplicate action PRs |

In-repo IDs already landed (strikethrough on the board — **do not reopen**):

`MIG-PROD` · `TLS-1` · `CORS-HTTPS` · `CD-1` (compose + dispatch; live promote still UNVERIFIED) · `COV-CRIT` · `PERF-1` · `A11Y-1` · `MIG-SEC` · `REV-62` · `P1-3b-RT` · `P1-10` · `P2-OBS` · `TD-1` · `TD-4` · `ADV-SEC` · `COV-1a` · `COV-1b` · `REL-TRUTH` · `SAFETY-1`

Ops-drills on tip `1b42ab4`: GitHub run **`31968740247` SUCCESS**. First post-#89 runs on `e05e29f` failed TLS (`docker exec chown` / `CERTIFICATE_VERIFY_FAILED`); **#94 fixed that**. Do not open a third TLS-proof PR.

---

## In flight — do not start a second copy

| Item | State | Owner rule |
|---|---|---|
| PR **#95** `feat/p1-critical-test-depth` | rebase / CI; do not invent new floors above measured CI | one agent only |
| PR **#92** Dependabot `github-actions` | MERGEABLE; must be up to date with `main` before merge | one agent only |
| `main` CI `1b42ab4` run `31968735637` | watch only | do not re-dispatch unless red |
| PR **#86** React 19 | **do not merge** | leave open |

---

## Still open — human / AWS / legal only

These cannot be closed from this repository. Packets and scripts exist;
status stays **UNVERIFIED** until a human or live AWS run records evidence.

| ID | Why an agent cannot close it |
|---|---|
| **HAND-1** | Empty signature table in `docs/ops/HAND1_BROWSER_PROOF.md`. Playwright covers the flows; a human must click and sign. **Do not agent-sign.** |
| **P1-11** | Independent ASVS L2 / pentest. `docs/ops/PENTEST_BRIEF.md` is the packet. |
| **P2-3-IAM** | Real AWS KMS alias / IAM / rotation. Verifier exits 2 without credentials. |
| **P1-3b-PROD** | Real AWS S3 bucket + policy + block public access + SSE-KMS. MinIO is not AWS. |
| **P1-10-PROD** | Off-host WAL + measured RPO on the production host. Local PITR is not this. |
| **P2-OBS-PROD** | Real pager receiver from a secret + tracing. Null-receiver drill is not this. |
| **KVKK / legal** | `docs/ops/LEGAL_APPROVAL.md` |
| **Live HA** | `ops/ha/live_check.sh` + `docs/ops/HA_TOPOLOGY.md` |
| **LICENSE** | `docs/ops/REPO_VISIBILITY.md` — public-repo licence decision is human |
| **ISO-1** | IsolationProvider — keep the abstraction, do **not** invent an implementation |
| **Scope.LOCATION** | Deliberately deferred. Do not open. |

Index of UNVERIFIED rows: `docs/ops/EXTERNAL_GATES.md`.

---

## Explicit non-claims (repeat these, do not “fix” them)

- Production-ready is **NO**.
- Phase 26 CORE MVP EXIT GATE is **NOT PASSED**.
- ASVS L2 report is a self-assessment, not an audit.
- Local MinIO / local PITR / null-receiver alert ≠ production evidence.
- Merge gate is **CI only** (review requirement removed 2026-08-16, single maintainer). Independent security APPROVE is a different gate (P1-11).

---

## CI discipline (2026-08-16)

Required CI is the merge gate and it is **expensive**. This wave burned
duplicate runs by rebasing `#95`/`#96` after every tip move and leaving
superseded workflows running.

- Do **not** rebase a PR that is already All Green unless merge is blocked
  by “not up to date” **and** you are about to merge it.
- Do **not** open a sibling PR for the same ID. Watch the existing run.
- Do **not** push docs-only follow-ups onto a PR whose unit job is still
  running — that cancels ~10 minutes of work.
- After a rebase, `gh run cancel` the previous SHA’s in-progress run.
- Prefer one PR, one CI, merge. Finish the product first; do not farm CI.

---

## Wave close (2026-08-16, docs)

In-repo certification wave is **closed**. Architecture (`docs/ARCHITECTURE.md`)
and `.codesight/wiki/` were refreshed against `1b42ab4`. The next step is a
**human live test** — not another agent rewrite of TLS / coverage / migrate /
ops-drills. After live test: HAND-1 signature + external gates.

---

## How the next agent should start

1. Read this file + `docs/HANDOFF.md` + `docs/PROGRESS_CHECKLIST.md`.
2. `git fetch` and treat `origin/main` as authority. Last code must match `git log -1 origin/main`.
3. If an ID is in the closed table above, **stop**. Tick it if a checklist still shows `[ ]`; do not write new code.
4. If a PR is in flight, **watch it**. Rebase only when merge is blocked
   and you will merge immediately. Do not open a sibling. Do not farm CI.
5. After `#95` lands, remaining agent-doable work is none in-repo.
   Human live test + HAND-1 + external gates. Refuse IsolationProvider /
   Scope.LOCATION / React 19 / HAND-1 signatures.
