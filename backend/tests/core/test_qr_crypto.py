"""Unit tests for QR compact token crypto (no DB)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.qr_crypto import (
    QrCryptoError,
    build_payload,
    new_local_hmac_ref,
    sign_payload,
    verify_and_decode,
)


def test_roundtrip_sign_verify():
    ref = new_local_hmac_ref()
    tenant_id = uuid4()
    member_id = uuid4()
    now = datetime.now(UTC)
    payload = build_payload(
        kid="qr-test",
        credential_id=str(uuid4()),
        jti="jti-1",
        iat=now,
        exp=now + timedelta(seconds=60),
        aud="access",
        tenant_id=tenant_id,
        member_id=member_id,
    )
    token = sign_payload(payload, ref)
    out = verify_and_decode(token, ref, expected_tenant_id=tenant_id)
    assert out["jti"] == "jti-1"
    assert out["member_id"] == str(member_id)


def test_missing_jti_rejected_at_build():
    now = datetime.now(UTC)
    with pytest.raises(QrCryptoError):
        build_payload(
            kid="k",
            credential_id="c",
            jti="",
            iat=now,
            exp=now + timedelta(seconds=30),
            aud="access",
            tenant_id=uuid4(),
            member_id=uuid4(),
        )


def test_expired_token():
    ref = new_local_hmac_ref()
    tenant_id = uuid4()
    now = datetime.now(UTC)
    payload = build_payload(
        kid="k",
        credential_id="c",
        jti="j",
        iat=now - timedelta(seconds=120),
        exp=now - timedelta(seconds=60),
        aud="access",
        tenant_id=tenant_id,
        member_id=uuid4(),
    )
    token = sign_payload(payload, ref)
    with pytest.raises(QrCryptoError, match="token_expired"):
        verify_and_decode(token, ref, expected_tenant_id=tenant_id, now=now)


def test_tampered_signature():
    ref = new_local_hmac_ref()
    tenant_id = uuid4()
    now = datetime.now(UTC)
    payload = build_payload(
        kid="k",
        credential_id="c",
        jti="j",
        iat=now,
        exp=now + timedelta(seconds=60),
        aud="access",
        tenant_id=tenant_id,
        member_id=uuid4(),
    )
    token = sign_payload(payload, ref)
    body, sig = token.split(".")
    bad = body + "." + ("A" * len(sig))
    with pytest.raises(QrCryptoError, match="invalid_signature"):
        verify_and_decode(bad, ref, expected_tenant_id=tenant_id)


def test_tenant_mismatch():
    ref = new_local_hmac_ref()
    tenant_id = uuid4()
    now = datetime.now(UTC)
    payload = build_payload(
        kid="k",
        credential_id="c",
        jti="j",
        iat=now,
        exp=now + timedelta(seconds=60),
        aud="access",
        tenant_id=tenant_id,
        member_id=uuid4(),
    )
    token = sign_payload(payload, ref)
    with pytest.raises(QrCryptoError, match="tenant_mismatch"):
        verify_and_decode(token, ref, expected_tenant_id=uuid4())
