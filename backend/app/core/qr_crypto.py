"""QR credential compact token crypto (HMAC-SHA256).

Token format: ``base64url(json_payload).base64url(hmac_sha256)``

Payload MUST include ``exp`` and ``jti`` (MASTER_SPEC fitness).
``key_material`` reference formats:
  - ``local:hmac:<urlsafe-base64-secret>``  (pre-prod / tests only)
  - any other string treated as opaque ref (not resolvable here → error)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

LOCAL_HMAC_PREFIX = "local:hmac:"
KMS_ENC_PREFIX = "kms:enc:"
KMS_ALIAS_PREFIX = "kms:alias/"
KMS_MOCK_PREFIX = "kms:mock:"
DEFAULT_ALGORITHM = "HMAC_SHA256"
REQUIRED_CLAIMS = frozenset(
    {"kid", "credential_id", "jti", "iat", "exp", "aud", "tenant_id", "member_id"}
)


class QrCryptoError(ValueError):
    """Invalid token structure, signature, or claims."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(data + pad)
    except Exception as e:
        raise QrCryptoError("invalid_token_encoding") from e


def _get_kms_client() -> Any:
    import boto3
    from botocore.config import Config  # type: ignore[import-untyped]

    return boto3.client(
        "kms",
        config=Config(connect_timeout=5, read_timeout=5, retries={"max_attempts": 2}),
    )


def new_local_hmac_ref() -> str:
    """Generate a HMAC secret reference using envelope encryption or local secret.

    When QR_KMS_MODE=aws_kms: Generates a data key via AWS KMS, stores the CiphertextBlob
    in the reference (kms:enc:<b64>), and uses the decrypted key for HMAC.
    """
    mode = os.environ.get("QR_KMS_MODE", "local").strip().lower()

    if mode == "aws_kms":
        from botocore.exceptions import (  # type: ignore[import-untyped]
            BotoCoreError,
            ClientError,
        )

        key_id = (os.environ.get("AWS_KMS_KEY_ID") or "").strip()
        if not key_id:
            raise QrCryptoError("missing_aws_kms_key_id")
        try:
            client = _get_kms_client()
            resp = client.generate_data_key(KeyId=key_id, KeySpec="AES_256")
        except (BotoCoreError, ClientError) as e:
            raise QrCryptoError(f"kms_generate_data_key_failed: {e}") from e
        ciphertext_blob: bytes = resp["CiphertextBlob"]
        return f"{KMS_ENC_PREFIX}{_b64url_encode(ciphertext_blob)}"

    if mode in {"kms", "mock"}:
        return f"{KMS_MOCK_PREFIX}qr-key-{uuid4().hex[:8]}"

    # Local or mock default
    raw = secrets.token_bytes(32)
    return f"{LOCAL_HMAC_PREFIX}{_b64url_encode(raw)}"


def resolve_hmac_secret(key_material: str) -> bytes:
    """Deterministically resolves the plaintext HMAC secret from the key reference.

    For kms:enc:<ciphertext>, calls KMS Decrypt to recover the original plaintext key.
    For local:hmac:<secret>, decodes the base64url secret bytes.
    """
    kms_mode = os.environ.get("QR_KMS_MODE", "local").strip().lower()

    if key_material.startswith(KMS_ENC_PREFIX):
        if kms_mode == "aws_kms":
            from botocore.exceptions import (  # type: ignore[import-untyped]
                BotoCoreError,
                ClientError,
            )

            ciphertext = _b64url_decode(key_material[len(KMS_ENC_PREFIX) :])
            try:
                client = _get_kms_client()
                resp = client.decrypt(CiphertextBlob=ciphertext)
                plaintext: bytes = resp["Plaintext"]
                if len(plaintext) < 16:
                    raise QrCryptoError("invalid_kms_plaintext_length")
                return plaintext
            except (BotoCoreError, ClientError) as e:
                raise QrCryptoError(f"kms_decryption_failed: {e}") from e
        if kms_mode in {"mock", "local", "test"}:
            return hashlib.sha256(key_material.encode("utf-8")).digest()
        raise QrCryptoError(
            f"Unsupported KMS mode '{kms_mode}' for encrypted key resolution"
        )

    if key_material.startswith((KMS_ALIAS_PREFIX, KMS_MOCK_PREFIX)):
        if kms_mode in {"mock", "local", "test", "kms"}:
            return hashlib.sha256(key_material.encode("utf-8")).digest()
        raise QrCryptoError(
            f"Unsupported KMS mode '{kms_mode}' for alias key material resolution"
        )

    if not key_material.startswith(LOCAL_HMAC_PREFIX):
        raise QrCryptoError("unsupported_key_material_ref")

    return _b64url_decode(key_material[len(LOCAL_HMAC_PREFIX) :])


def build_payload(
    *,
    kid: str,
    credential_id: str,
    jti: str,
    iat: datetime,
    exp: datetime,
    aud: str,
    tenant_id: UUID,
    member_id: UUID,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not jti or not exp:
        raise QrCryptoError("missing_exp_or_jti")
    payload: dict[str, Any] = {
        "kid": kid,
        "credential_id": credential_id,
        "jti": jti,
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "aud": aud,
        "tenant_id": str(tenant_id),
        "member_id": str(member_id),
    }
    if extra:
        for k, v in extra.items():
            if k not in payload:
                payload[k] = v
    missing = REQUIRED_CLAIMS - payload.keys()
    if missing:
        raise QrCryptoError(f"missing_claims:{sorted(missing)}")
    if payload.get("exp") is None or not payload.get("jti"):
        raise QrCryptoError("missing_exp_or_jti")
    return payload


def sign_payload(payload: dict[str, Any], key_material: str) -> str:
    secret = resolve_hmac_secret(key_material)
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body_b64 = _b64url_encode(body)
    sig = hmac.new(secret, body_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{body_b64}.{_b64url_encode(sig)}"


def verify_and_decode(
    token: str,
    key_material: str,
    *,
    expected_tenant_id: UUID,
    expected_aud: str = "access",
    now: datetime | None = None,
    leeway_seconds: int = 30,
) -> dict[str, Any]:
    if not token or "." not in token:
        raise QrCryptoError("malformed_token")
    parts = token.split(".")
    if len(parts) != 2:
        raise QrCryptoError("malformed_token")
    body_b64, sig_b64 = parts
    secret = resolve_hmac_secret(key_material)
    expected_sig = hmac.new(secret, body_b64.encode("ascii"), hashlib.sha256).digest()
    given_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, given_sig):
        raise QrCryptoError("invalid_signature")

    try:
        payload = json.loads(_b64url_decode(body_b64))
    except Exception as e:
        raise QrCryptoError("invalid_payload") from e
    if not isinstance(payload, dict):
        raise QrCryptoError("invalid_payload")

    missing = REQUIRED_CLAIMS - payload.keys()
    if missing:
        raise QrCryptoError(f"missing_claims:{sorted(missing)}")
    if not payload.get("jti") or payload.get("exp") is None:
        raise QrCryptoError("missing_exp_or_jti")

    if str(payload["tenant_id"]) != str(expected_tenant_id):
        raise QrCryptoError("tenant_mismatch")
    if payload.get("aud") != expected_aud:
        raise QrCryptoError("aud_mismatch")

    now = now or datetime.now(UTC)
    now_ts = int(now.timestamp())
    exp = int(payload["exp"])
    iat = int(payload["iat"])
    if now_ts > exp + leeway_seconds:
        raise QrCryptoError("token_expired")
    if iat > now_ts + leeway_seconds:
        raise QrCryptoError("token_not_yet_valid")

    return payload
