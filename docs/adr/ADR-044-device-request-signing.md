# ADR-044 — Device Request Signing (HMAC + Nonce) for the Edge Scanner Channel

- **Status:** Accepted
- **Date:** 2026-08-12
- **Supersedes:** none
- **Related:** ADR-031 Authentication & Session Strategy, ADR-013 Hybrid Tenant Isolation
- **Driver:** Phase 27.1 — the ASVS L2 self-assessment carried one open gap: the device channel had no request signing, so a stolen `device_session` cookie was a complete credential for 30 days.

## Context

A provisioned scanner authenticates once with `{device_id, tenant_id, api_key}`
and receives a `device_session` cookie (`POST /api/v1/devices/auth`). Every
later call to `POST /api/v1/devices/qr/validate` was authorized by that cookie
alone.

That is a weak position for this particular principal:

- The credential sits on an unattended tablet at a turnstile, in a semi-public
  space, typically kiosk-mode Chrome. Physical access to the device is part of
  the threat model, not an edge case.
- It is a bearer token with a 30-day lifetime. Copying it once yields the
  ability to grant gym entry — the device channel writes `access_attempts` and
  `checkins` and consumes entitlements.
- The device channel is the one path that *bypasses* the staff RBAC matrix by
  design: the endpoint substitutes the trusted device's own `device_id` and
  `location_id`, so possession of the cookie is possession of a location.

Revocation exists (`POST /devices/revoke`) but is reactive — it only helps after
someone notices.

## Decision

Split the device credential into two parts that do not travel together.

1. `POST /devices/auth` returns, in the **response body**, a per-session signing
   secret alongside the cookie. The secret is stored on the session row as a
   `local:hmac:…` reference (the same `key_material` convention as tenant QR
   signing keys, `app/core/qr_crypto.py`) and is never accepted back over the
   wire.
2. Every device request must carry three headers:

   ```
   X-Device-Timestamp: <unix seconds>
   X-Device-Nonce:     <16–128 chars of device randomness>
   X-Device-Signature: hex(HMAC-SHA256(secret, canonical))
   ```

   where the canonical string is

   ```
   <METHOD>\n<path>\n<timestamp>\n<nonce>\n<sha256-hex of raw body>
   ```

3. The timestamp must be within ±300s of server time, and the nonce must be
   unseen — claimed in `device_nonces` under a unique constraint, retained for
   twice the skew window.

Verification lives in `app/api/deps.py::_verify_device_signature`, called by
`get_current_device` after tenant context is established.

## Consequences

- A stolen cookie alone is useless: the attacker cannot produce a signature.
  Cookie theft and secret theft are now two separate compromises (the DB holds
  the secret but only a *hash* of the token; the cookie jar holds the token but
  not the secret).
- A signed request captured on the wire cannot be replayed — the nonce is spent
  and the timestamp expires.
- Body tampering is detected: the digest covers the exact bytes sent.
- **Sessions issued before this change fail closed** (`401
  device_session_unsigned`) rather than falling back to cookie-only trust. Every
  deployed device must re-authenticate once.
- Clock drift on a scanner beyond 5 minutes breaks it. That is deliberate: a
  wider window is a wider replay window, and NTP is a solved problem on the
  tablets we ship.
- XSS on the scanner origin still defeats this — the secret is reachable from
  the page. Signing raises the bar from "copy a cookie" to "run code on the
  device"; it does not replace the CSP and origin controls.

## Alternatives rejected

- **Derive the secret from a server-wide key** (`HMAC(SECRET_KEY, session_id)`).
  No secret at rest, but it introduces a new global key whose compromise forges
  every device, and the project has no secret-manager wiring for it yet.
- **Sign with the device `api_key`.** The server stores only its SHA-256 hash,
  so it cannot compute the HMAC — and un-hashing the stored key to enable that
  would be a clear regression.
- **mTLS.** Correct long-term answer for turnstile hardware, but it needs a
  certificate lifecycle (issuance, rotation, revocation, distribution) that does
  not exist yet. Signing is the useful subset available today.
- **Shorten the session lifetime instead.** Narrows the window without closing
  the hole, and forces re-pairing on unattended hardware.
