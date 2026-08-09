# Phase 13 — Real QR & Access Engine

**Status:** 🟢 LOCKED (PR #20 merge `babc33c`)  
**Depends on:** Phase 12 LOCKED (Idempotency)  
**Migrations:** `i2b3c4d5e6f7` (QR/access expand) + `j3c4d5e6f7a8` (access permissions)

## Spec anchors (MASTER_SPEC)

- Dynamic short-lived signed QR with `kid`, `credential_id`, `jti`, `iat`, `exp`, `aud`, `tenant`
- Key lifecycle: `ACTIVE` → `VERIFY_ONLY` → `REVOKED`
- Replay protection on `jti` (tenant-scoped)
- No token without `exp` / `jti`
- Secrets as references (dev: `local:hmac:…`; prod: KMS/Vault path)
- Access path: verify → entitlement check → AccessAttempt (+ optional Checkin)

## Design

```text
issue_qr
  → active SigningKey (HMAC_SHA256)
  → compact token: b64url(payload).b64url(sig)

validate_qr
  → parse + verify sig (ACTIVE|VERIFY_ONLY)
  → exp / tenant / aud
  → insert QrJtiReplay UNIQUE(tenant_id,jti)  → REPLAY deny
  → EntitlementService.check_access (optional consume)
  → AccessAttempt + Checkin (if location)
```

## Schema

| Object | Notes |
|--------|--------|
| `signing_keys` | UNIQUE(tenant_id, kid); `algorithm` column |
| `qr_jti_replays` | tenant-owned; UNIQUE(tenant_id, jti); RLS |
| `access_attempts` | expand: `jti`, `method` |

## API

- `POST /access/qr/issue` — `access:issue`
- `POST /access/qr/validate` — `access:validate`
- `POST /access/keys/rotate` — `access:keys`
- `GET /access/keys` — `access:keys`

## Deferred

- Device adapter / ZKTeco / OSDP
- Offline snapshot TTL policy full engine
- Client-side QR shell without server mint (forbidden for live credentials)
- KMS-backed key material

## Exit criteria

- Replay test green
- Rotation VERIFY_ONLY still verifies; REVOKED denies
- Real PG service tests + CI
