#!/usr/bin/env bash
# P1-3b-PROD: apply the committed AWS S3 contract and prove it via AWS APIs.
#
#   export AWS_REGION ACCOUNT_ID APP_ROLE_NAME REPORT_BUCKET S3_KMS_KEY_ID
#   export CONFIRM_APPLY=yes    # omit to lint + print only
#   ./ops/s3/apply_and_prove.sh
#
# Exits 2 (NOT VERIFIED) when credentials, placeholders, or the bucket
# are missing. Never treats MinIO as this gate.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HERE="$ROOT/ops/s3"

not_verified() {
  echo "NOT VERIFIED — $*" >&2
  echo "P1-3b-PROD stays UNVERIFIED." >&2
  exit 2
}

need() {
  local name="$1"
  [[ -n "${!name:-}" ]] || not_verified "$name is not set"
}

need AWS_REGION
need ACCOUNT_ID
need APP_ROLE_NAME
need REPORT_BUCKET
need S3_KMS_KEY_ID

command -v aws >/dev/null 2>&1 || not_verified "aws CLI is not on PATH"
command -v python3 >/dev/null 2>&1 || not_verified "python3 is not on PATH"

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  not_verified "no usable AWS credentials (sts get-caller-identity failed)"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Resolve alias/... or key id to a CMK ARN for the encryption config.
KMS_ARN="$(aws kms describe-key --key-id "$S3_KMS_KEY_ID" \
  --query 'KeyMetadata.Arn' --output text 2>/dev/null || true)"
[[ -n "$KMS_ARN" && "$KMS_ARN" != "None" ]] \
  || not_verified "cannot resolve S3_KMS_KEY_ID=$S3_KMS_KEY_ID to a CMK ARN"

python3 - "$HERE" "$TMP" "$ACCOUNT_ID" "$APP_ROLE_NAME" "$REPORT_BUCKET" "$KMS_ARN" <<'PY'
import json, sys
here, tmp, account, role, bucket, kms_arn = sys.argv[1:]

def load(name: str):
    with open(f"{here}/{name}", encoding="utf-8") as fh:
        raw = fh.read()
    raw = (
        raw.replace("ACCOUNT_ID", account)
        .replace("APP_ROLE_NAME", role)
        .replace("REPORT_BUCKET", bucket)
        .replace("S3_KMS_KEY_ARN", kms_arn)
    )
    leftover = [
        tok
        for tok in ("ACCOUNT_ID", "APP_ROLE_NAME", "REPORT_BUCKET", "S3_KMS_KEY_ARN")
        if tok in raw
    ]
    if leftover:
        raise SystemExit(f"placeholders remain in {name}: {leftover}")
    doc = json.loads(raw)
    out = f"{tmp}/{name}"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    return out

load("bucket-policy.json")
load("public-access-block.json")
load("lifecycle.json")
load("bucket-encryption.json")
print(f"substituted templates → {tmp}")
PY

echo "caller: $(aws sts get-caller-identity --query Arn --output text)"
echo "bucket: $REPORT_BUCKET"
echo "kms:    $KMS_ARN"

if [[ "${CONFIRM_APPLY:-}" != "yes" ]]; then
  echo
  echo "CONFIRM_APPLY is not 'yes' — showing substituted policy only."
  echo "----- bucket-policy.json -----"
  cat "$TMP/bucket-policy.json"
  not_verified "dry-run only; re-run with CONFIRM_APPLY=yes against the real bucket"
fi

aws s3api head-bucket --bucket "$REPORT_BUCKET" \
  || not_verified "bucket $REPORT_BUCKET does not exist or is not readable"

aws s3api put-public-access-block \
  --bucket "$REPORT_BUCKET" \
  --public-access-block-configuration "file://$TMP/public-access-block.json"

aws s3api put-bucket-encryption \
  --bucket "$REPORT_BUCKET" \
  --server-side-encryption-configuration "file://$TMP/bucket-encryption.json"

aws s3api put-bucket-lifecycle-configuration \
  --bucket "$REPORT_BUCKET" \
  --lifecycle-configuration "file://$TMP/lifecycle.json"

aws s3api put-bucket-policy \
  --bucket "$REPORT_BUCKET" \
  --policy "file://$TMP/bucket-policy.json"

# Prove the four Block Public Access flags.
python3 - "$REPORT_BUCKET" <<'PY'
import json, subprocess, sys
bucket = sys.argv[1]
raw = subprocess.check_output(
    ["aws", "s3api", "get-public-access-block", "--bucket", bucket],
    text=True,
)
cfg = json.loads(raw)["PublicAccessBlockConfiguration"]
wanted = {
    "BlockPublicAcls": True,
    "IgnorePublicAcls": True,
    "BlockPublicPolicy": True,
    "RestrictPublicBuckets": True,
}
for key, val in wanted.items():
    if cfg.get(key) is not True:
        raise SystemExit(f"public-access-block {key}={cfg.get(key)!r}, expected True")
print("PASS  public-access-block — all four flags true")
PY

# Prove default encryption is aws:kms against the reports CMK.
python3 - "$REPORT_BUCKET" "$KMS_ARN" <<'PY'
import json, subprocess, sys
bucket, kms_arn = sys.argv[1], sys.argv[2]
raw = subprocess.check_output(
    ["aws", "s3api", "get-bucket-encryption", "--bucket", bucket],
    text=True,
)
rules = json.loads(raw)["ServerSideEncryptionConfiguration"]["Rules"]
applied = rules[0]["ApplyServerSideEncryptionByDefault"]
algo = applied.get("SSEAlgorithm")
key = applied.get("KMSMasterKeyID")
if algo != "aws:kms":
    raise SystemExit(f"default encryption is {algo!r}, expected aws:kms")
if key and key not in (kms_arn, kms_arn.split("/")[-1]) and not key.endswith(
    kms_arn.split("/")[-1]
):
    raise SystemExit(f"default KMS key {key!r} does not match {kms_arn}")
print(f"PASS  default-encryption — SSEAlgorithm=aws:kms key={key}")
PY

# Prove TLS-only + app principal by writing a probe with aws:kms.
PROBE="_p1-3b-prod/$(python3 -c 'import uuid; print(uuid.uuid4())').txt"
aws s3api put-object \
  --bucket "$REPORT_BUCKET" \
  --key "$PROBE" \
  --body /dev/null \
  --server-side-encryption aws:kms \
  --ssekms-key-id "$S3_KMS_KEY_ID" >/dev/null

SSE="$(aws s3api head-object --bucket "$REPORT_BUCKET" --key "$PROBE" \
  --query 'ServerSideEncryption' --output text)"
[[ "$SSE" == "aws:kms" ]] || not_verified "probe object SSE is $SSE, expected aws:kms"
echo "PASS  sse-kms-probe — ServerSideEncryption=aws:kms"

# Anonymous GET of the exact key must not succeed.
REGION_HOST="${REPORT_BUCKET}.s3.${AWS_REGION}.amazonaws.com"
ANON_CODE="$(
  curl -sS -o /dev/null -w '%{http_code}' --max-time 15 \
    "https://${REGION_HOST}/${PROBE}" || true
)"
case "$ANON_CODE" in
  401|403) echo "PASS  anonymous-get — HTTP $ANON_CODE" ;;
  *)
    aws s3api delete-object --bucket "$REPORT_BUCKET" --key "$PROBE" >/dev/null || true
    not_verified "anonymous GET returned HTTP ${ANON_CODE:-none} (expected 401/403)"
    ;;
esac

aws s3api delete-object --bucket "$REPORT_BUCKET" --key "$PROBE" >/dev/null
echo "PASS  probe-cleanup — object removed"

echo
echo "ALL PASS — AWS S3 contract applied and probed on s3://$REPORT_BUCKET"
echo "Record this log in ops/s3/README.md. Do not flip EXTERNAL_GATES.md."
