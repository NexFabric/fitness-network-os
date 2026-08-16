"""Device signing secrets stay Fernet-wrapped at rest (ADR-044)."""

from __future__ import annotations

import os

from app.core.device_auth import (
    compute_signature,
    new_device_signing_material,
    verify_signature,
)
from app.core.qr_crypto import FERNET_HMAC_PREFIX, resolve_hmac_secret


def test_new_device_signing_material_is_fernet_prefixed():
    os.environ.setdefault("ENVIRONMENT", "test")
    ref, raw_secret = new_device_signing_material()
    assert ref.startswith(FERNET_HMAC_PREFIX)
    assert raw_secret
    assert FERNET_HMAC_PREFIX not in raw_secret
    assert raw_secret not in ref


def test_fernet_hmac_roundtrip_signs_and_verifies():
    os.environ.setdefault("ENVIRONMENT", "test")
    ref, _raw = new_device_signing_material()
    secret = resolve_hmac_secret(ref)
    assert isinstance(secret, bytes)
    assert len(secret) == 32

    presented = compute_signature(ref, "POST", "/api/v1/devices/qr/validate", "1", "n" * 16, b"{}")
    assert verify_signature(
        ref,
        presented,
        "POST",
        "/api/v1/devices/qr/validate",
        "1",
        "n" * 16,
        b"{}",
    )
    assert not verify_signature(
        ref,
        "0" * 64,
        "POST",
        "/api/v1/devices/qr/validate",
        "1",
        "n" * 16,
        b"{}",
    )
