#!/usr/bin/env bash
# Run Alembic to head. Any failure aborts the deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/backend"

if [[ -z "${DATABASE_URL:-}" && -z "${MIGRATOR_DATABASE_URL:-}" ]]; then
  echo "EVIDENCE-MISSING: DATABASE_URL or MIGRATOR_DATABASE_URL is required" >&2
  exit 1
fi

echo "alembic upgrade head"
exec uv run alembic upgrade head
