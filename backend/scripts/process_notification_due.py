#!/usr/bin/env python3
"""Ops entrypoint: retry FAILED notification deliveries for one tenant.

Not a public HTTP surface — intentional MVP. Wire via cron / worker / runbook.

Usage (from ``backend/``, with DATABASE_URL set):

  uv run python scripts/process_notification_due.py <tenant_uuid>
  uv run python scripts/process_notification_due.py <tenant_uuid> --limit 50 --max-attempts 5

Prints one JSON object on stdout: ``{"tenant_id": "...", "sent": N, "failed": N, "dead": N}``.
Exit 0 on success; non-zero on usage / runtime errors.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

# Allow ``uv run python scripts/...`` without installing package path hacks.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Default aligned with NotificationService.DEFAULT_MAX_ATTEMPTS (avoid import at --help).
_DEFAULT_MAX_ATTEMPTS = 5


async def process_due_for_tenant(
    session,
    tenant_id: UUID,
    *,
    limit: int = 50,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
) -> dict[str, int]:
    """Set tenant RLS context, run ``process_due_failed``, commit, return stats."""
    from sqlalchemy import text

    from app.api.deps import current_tenant_id_var
    from app.services.notification import NotificationService

    token = current_tenant_id_var.set(tenant_id)
    try:
        await session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
        svc = NotificationService(session)
        stats = await svc.process_due_failed(
            tenant_id, limit=limit, max_attempts=max_attempts
        )
        await session.commit()
        return stats
    except Exception:
        await session.rollback()
        raise
    finally:
        current_tenant_id_var.reset(token)


async def _async_main(
    tenant_id: UUID,
    *,
    limit: int,
    max_attempts: int,
) -> dict:
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        stats = await process_due_for_tenant(
            session,
            tenant_id,
            limit=limit,
            max_attempts=max_attempts,
        )
    return {"tenant_id": str(tenant_id), **stats}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Process due FAILED notification deliveries for one tenant "
            "(NotificationService.process_due_failed). Ops-only; no HTTP."
        )
    )
    p.add_argument(
        "tenant_id",
        type=UUID,
        help="Tenant UUID to process",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max deliveries to claim (1–100; service clamps). Default: 50",
    )
    p.add_argument(
        "--max-attempts",
        type=int,
        default=_DEFAULT_MAX_ATTEMPTS,
        help=f"Max attempt_count before DEAD. Default: {_DEFAULT_MAX_ATTEMPTS}",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.limit < 1:
        print("error: --limit must be >= 1", file=sys.stderr)
        return 2
    if args.max_attempts < 1:
        print("error: --max-attempts must be >= 1", file=sys.stderr)
        return 2
    try:
        result = asyncio.run(
            _async_main(
                args.tenant_id,
                limit=args.limit,
                max_attempts=args.max_attempts,
            )
        )
    except Exception as exc:  # pragma: no cover - surface ops errors
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
