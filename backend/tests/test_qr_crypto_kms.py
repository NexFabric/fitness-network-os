import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.qr_crypto import (
    DEFAULT_ALGORITHM,
    LOCAL_HMAC_PREFIX,
    QrCryptoError,
    build_payload,
    new_local_hmac_ref,
    resolve_hmac_secret,
    sign_payload,
    verify_and_decode,
)


def test_qr_crypto_local_mode():
    os.environ["QR_KMS_MODE"] = "local"
    key_ref = new_local_hmac_ref()
    assert key_ref.startswith(LOCAL_HMAC_PREFIX)

    secret = resolve_hmac_secret(key_ref)
    assert isinstance(secret, bytes)
    assert len(secret) == 32

    tenant_id = uuid4()
    member_id = uuid4()
    now = datetime.now(UTC)

    payload = build_payload(
        kid="kid-01",
        credential_id="cred-01",
        jti=str(uuid4()),
        iat=now,
        exp=now + timedelta(minutes=5),
        aud="access",
        tenant_id=tenant_id,
        member_id=member_id,
    )
    token = sign_payload(payload, key_ref)
    decoded = verify_and_decode(token, key_ref, expected_tenant_id=tenant_id)
    assert decoded["kid"] == "kid-01"
    assert decoded["member_id"] == str(member_id)


def test_qr_crypto_kms_mock_mode():
    os.environ["QR_KMS_MODE"] = "mock"
    key_ref = "kms:mock:test-key"
    secret = resolve_hmac_secret(key_ref)
    assert isinstance(secret, bytes)
    assert len(secret) == 32

    tenant_id = uuid4()
    member_id = uuid4()
    now = datetime.now(UTC)

    payload = build_payload(
        kid="kid-kms",
        credential_id="cred-kms",
        jti=str(uuid4()),
        iat=now,
        exp=now + timedelta(minutes=5),
        aud="access",
        tenant_id=tenant_id,
        member_id=member_id,
    )
    token = sign_payload(payload, key_ref)
    decoded = verify_and_decode(token, key_ref, expected_tenant_id=tenant_id)
    assert decoded["kid"] == "kid-kms"


def test_qr_crypto_envelope_mock_mode():
    os.environ["QR_KMS_MODE"] = "mock"
    key_ref = "kms:enc:bW9ja19jaXBoZXJfdGV4dA"
    secret = resolve_hmac_secret(key_ref)
    assert isinstance(secret, bytes)
    assert len(secret) == 32


def test_qr_crypto_unsupported_mode_raises():
    os.environ["QR_KMS_MODE"] = "invalid_mode"
    with pytest.raises(QrCryptoError):
        resolve_hmac_secret("kms:enc:bW9ja19jaXBoZXJfdGV4dA")
    # Reset back to local
    os.environ["QR_KMS_MODE"] = "local"
