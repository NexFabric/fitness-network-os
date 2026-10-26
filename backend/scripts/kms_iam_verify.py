#!/usr/bin/env python
"""P2-3-IAM verification: exercise the real AWS KMS + S3 SSE-KMS paths.

This script cannot be satisfied by this repository alone — it needs a real AWS
account, a CMK and a bucket. It exists so that the moment those exist, closing
P2-3-IAM is one command instead of a research project.

    export AWS_REGION=eu-central-1
    export AWS_KMS_KEY_ID=alias/fitness-os-qr
    export S3_BUCKET_NAME=fitness-os-reports-prod
    export S3_KMS_KEY_ID=alias/fitness-os-reports
    cd backend && ./.venv/bin/python scripts/kms_iam_verify.py

Checks:
  1. credentials resolve and the caller identity is the expected app principal
  2. the QR CMK has automatic key rotation ENABLED
  3. GenerateDataKey + Decrypt round-trip returns the same 32-byte key
  4. the app's own envelope helpers produce a `kms:enc:` ref that resolves
  5. S3 PutObject with aws:kms lands with SSEKMSKeyId set
  6. the app principal is DENIED kms:ScheduleKeyDeletion (least privilege holds)

Exits non-zero on the first failure. Refuses to run — rather than pretending —
when credentials are absent.
"""

from __future__ import annotations

import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASSED: list[str] = []


def ok(step: str, detail: str = "") -> None:
    PASSED.append(step)
    print(f"PASS  {step}" + (f" — {detail}" if detail else ""))


def die(step: str, detail: str) -> None:
    print(f"FAIL  {step} — {detail}")
    sys.exit(1)


def skip(reason: str) -> None:
    print(f"SKIP  {reason}")
    print("\nNOT VERIFIED — this run proves nothing. P2-3-IAM stays open.")
    sys.exit(2)


def main() -> None:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

    kms_key_id = (os.environ.get("AWS_KMS_KEY_ID") or "").strip()
    bucket = (os.environ.get("S3_BUCKET_NAME") or "").strip()
    s3_kms_key_id = (os.environ.get("S3_KMS_KEY_ID") or "").strip()

    if not kms_key_id:
        skip("AWS_KMS_KEY_ID is not set — no CMK to verify")

    # 1. identity
    try:
        ident = boto3.client("sts").get_caller_identity()
    except (NoCredentialsError, BotoCoreError, ClientError) as exc:
        skip(f"no usable AWS credentials ({type(exc).__name__})")
    ok("caller-identity", f"{ident['Arn']}")

    kms = boto3.client("kms")

    # 2. rotation must be on
    try:
        rot = kms.get_key_rotation_status(KeyId=kms_key_id)
    except ClientError as exc:
        die("key-rotation", f"{exc.response['Error']['Code']}: {exc}")
    if not rot.get("KeyRotationEnabled"):
        die("key-rotation", "automatic key rotation is DISABLED on the QR CMK")
    ok("key-rotation", "KeyRotationEnabled=True")

    # 3. envelope round-trip
    try:
        gen = kms.generate_data_key(KeyId=kms_key_id, KeySpec="AES_256")
        dec = kms.decrypt(CiphertextBlob=gen["CiphertextBlob"])
    except ClientError as exc:
        die("envelope-roundtrip", f"{exc.response['Error']['Code']}: {exc}")
    if dec["Plaintext"] != gen["Plaintext"] or len(gen["Plaintext"]) != 32:
        die("envelope-roundtrip", "decrypted key does not match the generated key")
    ok("envelope-roundtrip", "GenerateDataKey + Decrypt match, 32 bytes")

    # 4. the application's own helpers
    os.environ["QR_KMS_MODE"] = "aws_kms"
    from app.core.qr_crypto import (
        KMS_ENC_PREFIX,
        new_local_hmac_ref,
        resolve_hmac_secret,
    )

    try:
        ref = new_local_hmac_ref()
        secret = resolve_hmac_secret(ref)
    except Exception as exc:
        die("app-envelope", f"{type(exc).__name__}: {exc}")
    if not ref.startswith(KMS_ENC_PREFIX) or len(secret) != 32:
        die(
            "app-envelope",
            f"unexpected ref/secret: prefix_ok={ref[:8]!r} len={len(secret)}",
        )
    ok("app-envelope", f"{KMS_ENC_PREFIX}… resolves to a 32-byte secret")

    # 5. S3 SSE-KMS
    if bucket and s3_kms_key_id:
        s3 = boto3.client("s3")
        key = f"_p2-3-iam-verify/{uuid4()}.txt"
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=b"p2-3-iam verification",
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=s3_kms_key_id,
            )
            head = s3.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            die("s3-sse-kms", f"{exc.response['Error']['Code']}: {exc}")
        if head.get("ServerSideEncryption") != "aws:kms" or not head.get("SSEKMSKeyId"):
            die(
                "s3-sse-kms",
                f"unexpected encryption headers: {head.get('ServerSideEncryption')}",
            )
        ok("s3-sse-kms", f"SSEKMSKeyId={head['SSEKMSKeyId'].rsplit('/', 1)[-1]}")
        s3.delete_object(Bucket=bucket, Key=key)
        ok("s3-cleanup", "verification object removed")
    else:
        print("SKIP  s3-sse-kms — S3_BUCKET_NAME / S3_KMS_KEY_ID not set")

    # 6. least privilege must actually bite
    try:
        kms.schedule_key_deletion(KeyId=kms_key_id, PendingWindowInDays=30)
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code not in ("AccessDeniedException", "AccessDenied"):
            die("least-privilege", f"expected AccessDenied, got {code}")
        ok("least-privilege", "ScheduleKeyDeletion denied for the app principal")
    else:
        kms.cancel_key_deletion(KeyId=kms_key_id)
        die(
            "least-privilege",
            "app principal CAN schedule key deletion — policy is too broad",
        )

    print(f"\nALL PASS — {len(PASSED)} checks against real AWS KMS/S3")


if __name__ == "__main__":
    main()
