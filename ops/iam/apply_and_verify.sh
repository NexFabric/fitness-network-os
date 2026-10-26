#!/usr/bin/env bash
# P2-3-IAM: substitute committed policies, optionally apply, then run
# backend/scripts/kms_iam_verify.py against real AWS.
#
#   export AWS_REGION ACCOUNT_ID APP_ROLE_NAME ADMIN_ROLE_NAME
#   export QR_CMK_KEY_ID S3_CMK_KEY_ID REPORT_BUCKET
#   export AWS_KMS_KEY_ID S3_BUCKET_NAME S3_KMS_KEY_ID
#   export CONFIRM_APPLY=yes    # omit = print + verify only (no Put*)
#   ./ops/iam/apply_and_verify.sh
#
# Exits 2 when credentials or placeholders are missing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HERE="$ROOT/ops/iam"

not_verified() {
  echo "NOT VERIFIED — $*" >&2
  echo "P2-3-IAM stays UNVERIFIED." >&2
  exit 2
}

need() {
  local name="$1"
  [[ -n "${!name:-}" ]] || not_verified "$name is not set"
}

need AWS_REGION
need ACCOUNT_ID
need APP_ROLE_NAME
need ADMIN_ROLE_NAME
need QR_CMK_KEY_ID
need S3_CMK_KEY_ID
need REPORT_BUCKET

# Verifier env — accept alias or key id; default to the runbook aliases.
export AWS_KMS_KEY_ID="${AWS_KMS_KEY_ID:-alias/fitness-os-qr}"
export S3_BUCKET_NAME="${S3_BUCKET_NAME:-$REPORT_BUCKET}"
export S3_KMS_KEY_ID="${S3_KMS_KEY_ID:-alias/fitness-os-reports}"

command -v aws >/dev/null 2>&1 || not_verified "aws CLI is not on PATH"
command -v python3 >/dev/null 2>&1 || not_verified "python3 is not on PATH"

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  not_verified "no usable AWS credentials (sts get-caller-identity failed)"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 - "$HERE" "$TMP" \
  "$ACCOUNT_ID" "$AWS_REGION" "$APP_ROLE_NAME" "$ADMIN_ROLE_NAME" \
  "$QR_CMK_KEY_ID" "$S3_CMK_KEY_ID" "$REPORT_BUCKET" <<'PY'
import json, sys
(
    here, tmp, account, region, app_role, admin_role,
    qr_key, s3_key, bucket,
) = sys.argv[1:]

tokens = {
    "ACCOUNT_ID": account,
    "REGION": region,
    "APP_ROLE_NAME": app_role,
    "ADMIN_ROLE_NAME": admin_role,
    "QR_CMK_KEY_ID": qr_key,
    "S3_CMK_KEY_ID": s3_key,
    "REPORT_BUCKET": bucket,
}

def subst(name: str) -> str:
    with open(f"{here}/{name}", encoding="utf-8") as fh:
        raw = fh.read()
    for tok, val in tokens.items():
        raw = raw.replace(tok, val)
    leftover = [tok for tok in tokens if tok in raw]
    if leftover:
        raise SystemExit(f"placeholders remain in {name}: {leftover}")
    doc = json.loads(raw)
    doc.pop("Comment", None)
    out = f"{tmp}/{name}"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    return out

subst("fitness-os-app-policy.json")
subst("fitness-os-kms-key-policy.json")
print(f"substituted templates → {tmp}")
PY

echo "caller: $(aws sts get-caller-identity --query Arn --output text)"

if [[ "${CONFIRM_APPLY:-}" == "yes" ]]; then
  echo "applying identity policy to role $APP_ROLE_NAME"
  aws iam put-role-policy \
    --role-name "$APP_ROLE_NAME" \
    --policy-name fitness-os-app \
    --policy-document "file://$TMP/fitness-os-app-policy.json"

  echo "applying key policy to QR CMK $QR_CMK_KEY_ID"
  aws kms put-key-policy \
    --key-id "$QR_CMK_KEY_ID" \
    --policy-name default \
    --policy "file://$TMP/fitness-os-kms-key-policy.json"

  echo "applying the same use/deny shape to reports CMK $S3_CMK_KEY_ID"
  # Reports CMK: same admin/app split. The identity policy already
  # scopes GenerateDataKey/Decrypt via s3.REGION.amazonaws.com.
  python3 - "$TMP/fitness-os-kms-key-policy.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    doc = json.load(fh)
doc["Id"] = "fitness-os-reports-cmk"
with open(path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
  aws kms put-key-policy \
    --key-id "$S3_CMK_KEY_ID" \
    --policy-name default \
    --policy "file://$TMP/fitness-os-kms-key-policy.json"
else
  echo "CONFIRM_APPLY is not 'yes' — skipping PutRolePolicy / PutKeyPolicy."
  echo "----- fitness-os-app-policy.json -----"
  cat "$TMP/fitness-os-app-policy.json"
fi

VERIFY="$ROOT/backend/scripts/kms_iam_verify.py"
if [[ ! -f "$VERIFY" ]]; then
  not_verified "missing $VERIFY"
fi

echo
echo "running $VERIFY"
if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  PY="$ROOT/backend/.venv/bin/python"
else
  PY="python3"
fi
cd "$ROOT/backend"
exec "$PY" "$VERIFY"
