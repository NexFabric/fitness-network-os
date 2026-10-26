# Staging rehearsal

**Date:** 2026-08-16
**Status:** **SCRIPTS LANDED · NO STAGING HOST · ALL TRACKS UNVERIFIED**

Read that status literally. This repository does not own a cloud account
and does not publish a reachable staging URL. The k6 files under
`ops/load/`, `backend/scripts/smtp_delivery_proof.py`, and
`ops/deploy/rollback.md` are the in-repo contract. Checking them in is
not evidence.

A human closes a track only by pasting output from a host they actually
control into the evidence tables at the bottom. Until then every status
line stays **UNVERIFIED**. Do not change those lines from intent, from
CI, or from a local Mailpit/dev-stack run.

## What this file is

Operator steps for three open P1 tracks:

1. k6 `qr_validate` / `class_book` / `finance_idempotency` against `$BASE_URL`
2. SMTP proof script plus DKIM / SPF / DMARC checklist
3. `migrate` → `smoke` → `rollback.md` rehearsal

## What this file is not

- A claimed capacity SLO or production RPS number
- A substitute for Phase 26 PASS or production-ready YES
- Permission to point k6 at production from a laptop
- An invented hostname (`api.staging.example.com` in `ops/load/README.md`
  is a placeholder, not a host this project runs)

Related in-repo contracts (none of them are this rehearsal):

| File | What it actually is |
|---|---|
| `ops/load/README.md` | k6 usage notes; says checking in is not evidence |
| `docs/ops/SMTP_PROOF.md` | Adapter landed · domain proof UNVERIFIED |
| `ops/deploy/README.md` | migrate → roll → smoke → abort |
| `ops/deploy/rollback.md` | Procedure landed · **NOT VERIFIED** |
| `docs/ops/PRODUCTION_DEPLOY.md` | In-repo gate landed · live deploy NOT VERIFIED |

## Preconditions — stop here if any fail

1. **You have a host.** This repo does not give you one. If you cannot
   name the machine and the URL, do not run anything. Status stays
   UNVERIFIED.
2. **`$BASE_URL` is not production** for the k6 track. Do not run these
   scripts against a live member-facing API from a workstation. A
   production load test is a change-controlled event on a dedicated
   runner, not this runbook.
3. **Auth material is real for that host** (`AUTH_TOKEN`, `TENANT_ID`,
   and the per-script IDs). Empty tokens against `127.0.0.1:8000` prove
   the harness starts, not that staging held.
4. k6 is installed on the operator machine (`k6 version`). The repo
   does not vendor a k6 binary.
5. You will paste **command + raw output**, not a paraphrase, into the
   evidence tables.

If you only have the laptop docker-compose stack, you may use it as a
**dry-run of the commands**. That dry-run does **not** flip any status
line in this file.

---

## Track 1 — k6 against `$BASE_URL`

**Status:** **UNVERIFIED**

These scripts are a capacity *rehearsal*. Default VUs are conservative
(`50` / `50` / `20`). Raising `VUS` does not create an SLO.

### Scripts

| Script | Default load | What it hits | Check |
|---|---|---|---|
| `ops/load/qr_validate.js` | 50 VUs / 30s | `POST /api/v1/access/qr/validate` | status `< 500` |
| `ops/load/class_book.js` | 50 VUs / 50 iterations | `POST /api/v1/classes/sessions/{id}/book` | `200/201/409/422` |
| `ops/load/finance_idempotency.js` | 20 VUs / 40 iterations | `POST /api/v1/finance/payments` + shared `Idempotency-Key` | status `< 500` |

`class_book` is last-seat contention: every VU books the **same**
session. `finance_idempotency` is a shared-key collision, not a
throughput test.

### Environment

Export only values that belong to the host you are about to hit.
Do not copy a production token into this shell.

```bash
# Required. Must be a URL you can name. Leave unset and stop if you
# do not have a non-production host.
export BASE_URL=          # e.g. https://<your-host>  — there is no default staging URL
export AUTH_TOKEN=
export TENANT_ID=

# qr_validate — a real short-lived QR from that tenant, not the script default
export QR_TOKEN=

# class_book — one session + one member that exist on that host
export SESSION_ID=
export MEMBER_ID=

# finance_idempotency — a real billing account; keep the key stable for the run
export BILLING_ACCOUNT_ID=
export IDEMPOTENCY_KEY=staging-rehearsal-pay-1
```

The scripts fall back to `http://127.0.0.1:8000` and
`QR_TOKEN=invalid-qr-for-burst` when those variables are empty. That
fallback is for local harness bring-up. It is **not** a staging result.

Optional knobs (still not an SLO):

```bash
export VUS=50
export DURATION=30s          # qr_validate only
export ITERATIONS=50         # class_book / finance
```

### Commands

From the repository root, on a machine that can reach `$BASE_URL`:

```bash
test -n "${BASE_URL:-}" || { echo "EVIDENCE-MISSING: BASE_URL unset — no staging host in this repo"; exit 1; }
case "$BASE_URL" in
  *gymclubnex.com*|*production*) echo "REFUSING: do not run this k6 track against production"; exit 1 ;;
esac

k6 version
k6 run ops/load/qr_validate.js
k6 run ops/load/class_book.js
k6 run ops/load/finance_idempotency.js
```

Run them one at a time. Keep the full k6 summary (checks, http_req_failed,
http_req_duration). Do not add these jobs as a required GitHub check —
`ops/load/README.md` already forbids that.

### How to read the output (do not force green)

k6 treats HTTP ≥ 400 as `http_req_failed`. That matters:

- `qr_validate` with an invalid / expired token will 4xx. The `check`
  (`< 500`) can pass while the `http_req_failed` threshold (`rate<0.05`)
  fails. That is a correct API, not a capacity pass.
- `class_book` last-seat 409/422 is the point of the script. Many 409s
  will trip `http_req_failed: rate<0.2` even when every request
  *settled*. Record both the check rate and the threshold result.
- `finance_idempotency` has no threshold. A useful run shows one
  payment created and the rest returning the idempotent replay (not
  5xx, not N independent charges). Confirm on the host that
  `amount_minor` was applied once.

A track is evidence only when:

1. `$BASE_URL` names a non-production host the operator controls
2. tokens / IDs were issued on that host
3. the three summaries are pasted below
4. the operator writes what the numbers mean (including failed
   thresholds that are expected 4xx)

A local `127.0.0.1` run, an empty `AUTH_TOKEN`, or a rewrite of the
thresholds to hide 4xx is **not** evidence.

---

## Track 2 — SMTP proof + DKIM / SPF / DMARC

**Status:** **UNVERIFIED** (adapter code landed; domain proof is not)

The script is `backend/scripts/smtp_delivery_proof.py`. It sends one
message with no PII and **does not** assert DKIM, SPF, or DMARC. Exit
`2` when `SMTP_HOST` is unset (`UNVERIFIED`). That exit code is not a
pass.

Companion checklist: `docs/ops/SMTP_PROOF.md`.

### 2a. Adapter send (necessary, not sufficient)

Against the **same SMTP the staging notification worker uses**, from
`backend/`:

```bash
export SMTP_HOST=            # real provider host — not 127.0.0.1 unless you are only proving the adapter
export SMTP_PORT=587
export SMTP_STARTTLS=1
export SMTP_USER=
export SMTP_PASS=
export SMTP_FROM=            # must be an address the provider will accept
export SMTP_PROOF_TO=        # mailbox you can open

uv run python scripts/smtp_delivery_proof.py
```

A successful run prints `SMTP proof: sent via …` and reminds you that
DKIM/SPF/DMARC are not asserted. Open the destination mailbox (or the
provider's accepted-message log) and keep the Message-ID.

Local Mailpit / Mailhog on `127.0.0.1:1025` with `SMTP_STARTTLS=0` is
**adapter proof only**. It does not close this track. Do not paste a
Mailpit send as staging evidence.

### 2b. Domain checklist (human)

Tick only from DNS / provider screenshots or `dig` output for the
**From:** domain you actually sent as. Leave the box empty if you did
not look.

- [ ] Real provider accepted the message (Message-ID: )
- [ ] SPF published for that From domain (`dig TXT <domain>`)
- [ ] DKIM signing on (selector + `dkim=pass` on the received copy)
- [ ] DMARC policy recorded (`_dmarc.<domain>`, policy + rua)
- [ ] Auth rejection path observed (bad password → worker does not
      report success)
- [ ] Bounce / retry observed on the notification worker

Until every box is ticked from a real domain, this track stays
UNVERIFIED even if the script printed `sent`.

---

## Track 3 — migrate → smoke → rollback rehearsal

**Status:** **UNVERIFIED** (`ops/deploy/rollback.md` is procedure
landed, not a tested rehearsal)

There is no staging compose target in this repository. You need a host
that already runs the production compose contract
(`docker-compose.prod.yml` or equivalent) and two image tags:

- **new:** the revision you are about to roll (`fitness-network-os:<new-sha>`)
- **previous:** last known-good (`fitness-network-os:<old-sha>`)

Workers must match the backend revision. Schema is expand-then-contract
(ADR-037). **Do not** `alembic downgrade` as the default recovery.

### 3a. Migrate (abort on failure)

On the host, with the migrator DSN only (not on long-lived API/workers):

```bash
export DATABASE_URL=              # or MIGRATOR_DATABASE_URL
# Prefer sslmode=require|verify-full. See docs/ops/PRODUCTION_DEPLOY.md.

ops/deploy/migrate.sh
```

Equivalent via compose: the one-shot `migrate` service must exit 0
before `backend` / workers start
(`depends_on: migrate: condition: service_completed_successfully`).

A failed migrate is a failed deploy. Do not start API or workers. Do
not continue to smoke.

Record: Alembic revision **before** and **after** (`alembic current`).
Expected head at time of writing: `xi0d1e2f3a4b`.

### 3b. Roll application, then smoke

Start backend, then workers, on the **new** image. Frontends may follow
once `/ready` is 200.

```bash
export SMOKE_BASE_URL=            # that host's API origin — no default staging URL
ops/deploy/smoke.sh
```

`smoke.sh` requires HTTP 200 from `/live` and `/ready`. Anything else
prints `SMOKE FAIL` and exits 1. `/live` means process up; `/ready`
means Postgres + Redis reachable.

Do not call smoke a rehearsal pass if you pointed it at
`http://127.0.0.1:8000` on a laptop compose stack.

### 3c. Rollback rehearsal (`ops/deploy/rollback.md`)

This is the part that is **NOT VERIFIED** until a real host records it.

1. Keep the last known-good digest (`fitness-network-os:<old-sha>`).
2. Stop the new backend and workers.
3. Start the previous image. Workers must match that backend revision.
4. Run `ops/deploy/smoke.sh` again against the same `SMOKE_BASE_URL`.
5. Leave the newer migration in place if it is backward-compatible.

If a CONTRACT migration shipped in the same release as code that still
reads the old shape, this is an **incident**, not a routine rollback:
restore from PITR / base backup (`docs/ops/DR_RESTORE_STATUS.md`,
`docs/ops/WAL_ARCHIVE.md`). Do not invent a downgrade path here.

A rollback rehearsal is evidence only when smoke is green on the
**previous** image after a real stop/start on that host, and the
operator records both image digests.

`.github/workflows/deploy.yml` is `workflow_dispatch` only. It builds
images and refuses success when deploy secrets are absent. It does not
invent a cloud target and does not replace this rehearsal.

---

## Evidence ledger

Paste only from a run you performed. Empty cell = UNVERIFIED.
Do not write PASS in the status column without a paste in the evidence
column.

### Track 1 — k6

| Field | Value |
|---|---|
| Status | **UNVERIFIED** |
| Date | |
| Operator | |
| `BASE_URL` (hostname only is fine; no secrets) | |
| Confirmed not production? | |
| `k6 version` | |
| `qr_validate.js` summary (paste) | |
| `class_book.js` summary (paste) | |
| `finance_idempotency.js` summary (paste) | |
| Single-charge confirmed for shared idempotency key? | |
| Notes (including expected 4xx vs real 5xx) | |

### Track 2 — SMTP / DNS

| Field | Value |
|---|---|
| Status | **UNVERIFIED** |
| Date | |
| Operator | |
| Provider + From domain | |
| Script output (paste) | |
| Message-ID / mailbox proof | |
| `dig` SPF (paste) | |
| DKIM selector + `dkim=` result | |
| `_dmarc` TXT (paste) | |
| Auth-reject observed? | |
| Bounce / retry observed? | |

### Track 3 — migrate / smoke / rollback

| Field | Value |
|---|---|
| Status | **UNVERIFIED** |
| Date | |
| Operator | |
| Host (name, not a made-up URL) | |
| Alembic before → after | |
| New image digest | |
| Previous image digest | |
| `migrate.sh` output (paste) | |
| `smoke.sh` on new image (paste) | |
| Rollback steps actually performed | |
| `smoke.sh` on previous image (paste) | |
| Newer migration left in place? | |

---

## What a fully pasted ledger would still not close

- Phase 26 CORE MVP EXIT GATE
- Production-ready YES
- Independent pentest (`docs/ops/PENTEST_BRIEF.md`)
- Real AWS S3 / KMS / IAM (`docs/ops/S3_RUNTIME_PROOF.md`,
  `docs/ops/KMS_IAM_RUNBOOK.md`)
- Off-host WAL + measured production RPO (`docs/ops/WAL_ARCHIVE.md`)
- HAND-1 human browser signature (`docs/ops/HAND1_BROWSER_PROOF.md`)
- Any capacity SLO (none is claimed here)
