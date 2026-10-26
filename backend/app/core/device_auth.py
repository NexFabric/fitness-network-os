"""Request signing for the edge scanner device channel (HMAC-SHA256 + nonce).

A ``device_session`` cookie on its own used to be a complete credential: anyone
who copied it off a turnstile tablet could call the device API for the whole
30-day session lifetime. Signing splits the credential in two — the session
token (sent as a cookie, replayable by anyone who steals it) and a per-session
signing secret (handed to the device once at ``POST /devices/auth``, stored by
the device, never sent on the wire again). A request is only accepted when the
caller proves possession of both, so cookie theft alone buys nothing.

Canonical string (newline-joined, no trailing newline)::

    <METHOD>\\n<path>\\n<unix-timestamp>\\n<nonce>\\n<sha256-hex of raw body>

The timestamp must be within ``MAX_CLOCK_SKEW_SECONDS`` of server time, and the
nonce must not have been seen before (``device_nonces``), which is what stops a
captured signed request from being replayed inside that window.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from app.core.qr_crypto import FERNET_HMAC_PREFIX, resolve_hmac_secret

# A signed request is accepted this far either side of server time. Scanner
# tablets drift; anything wider needlessly widens the replay window.
MAX_CLOCK_SKEW_SECONDS = 300
# Nonces are retained for twice the skew window, so a replay can never outlive
# the acceptance window of the timestamp it carries.
NONCE_RETENTION_SECONDS = 2 * MAX_CLOCK_SKEW_SECONDS

# Shortest nonce we accept. 16 chars of device-generated randomness makes an
# accidental collision (which would read as a replay) irrelevant.
MIN_NONCE_LENGTH = 16
MAX_NONCE_LENGTH = 128

SIGNATURE_HEADER = "X-Device-Signature"
TIMESTAMP_HEADER = "X-Device-Timestamp"
NONCE_HEADER = "X-Device-Nonce"


class DeviceSignatureError(ValueError):
    """The signing material or the presented signature is unusable."""


def new_device_signing_material() -> tuple[str, str]:
    """Return ``(key_material_ref, raw_secret)`` for a new device session.

    The ref is stored on the session row (Fernet-wrapped); the raw secret is
    returned to the device exactly once. Cookie theft still cannot sign.
    """
    raw = secrets.token_bytes(32)
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    from app.core.security import get_fernet

    wrapped = get_fernet().encrypt(raw).decode("ascii")
    return FERNET_HMAC_PREFIX + wrapped, encoded


def build_canonical_string(
    method: str, path: str, timestamp: str, nonce: str, body: bytes
) -> str:
    body_hash = hashlib.sha256(body).hexdigest()
    return f"{method.upper()}\n{path}\n{timestamp}\n{nonce}\n{body_hash}"


def compute_signature(
    key_material: str, method: str, path: str, timestamp: str, nonce: str, body: bytes
) -> str:
    secret = resolve_hmac_secret(key_material)
    canonical = build_canonical_string(method, path, timestamp, nonce, body)
    return hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(
    key_material: str,
    presented: str,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    body: bytes,
) -> bool:
    """Constant-time check of a presented signature against the expected one."""
    expected = compute_signature(key_material, method, path, timestamp, nonce, body)
    return hmac.compare_digest(expected, presented.strip().lower())
