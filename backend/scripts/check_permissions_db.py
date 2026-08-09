#!/usr/bin/env python3
"""Compare permissions.yml canonical matrix to migrated PostgreSQL roles/permissions.

Run AFTER `alembic upgrade head` with DATABASE_URL / MIGRATOR_DATABASE_URL pointing
at a real Postgres (CI test job).

Exit 0 = parity; non-zero = drift.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

try:
    import psycopg
except ImportError:  # pragma: no cover
    try:
        import psycopg2 as psycopg  # type: ignore
    except ImportError:
        print("psycopg/psycopg2 required for check_permissions_db", file=sys.stderr)
        sys.exit(2)


def _sync_dsn(url: str) -> str:
    return (
        url.replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgresql+psycopg://", "postgresql://")
    )


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    yaml_path = root / "permissions.yml"
    if not yaml_path.exists():
        print(f"missing {yaml_path}", file=sys.stderr)
        return 1

    data = yaml.safe_load(yaml_path.read_text())
    yaml_perms = {p["id"] for p in data.get("permissions", []) if p.get("id") != "*"}
    yaml_roles: dict[str, set[str]] = {}
    for role_name, role_data in (data.get("roles") or {}).items():
        perms = set(role_data.get("permissions") or [])
        perms.discard("*")
        yaml_roles[role_name] = perms

    dsn = _sync_dsn(
        os.environ.get("MIGRATOR_DATABASE_URL")
        or os.environ.get("TEST_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or ""
    )
    if not dsn:
        print("DATABASE_URL / TEST_DATABASE_URL / MIGRATOR_DATABASE_URL required", file=sys.stderr)
        return 2

    errors: list[str] = []
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT name FROM permissions")
        db_perms = {r[0] for r in cur.fetchall()}
        missing_in_db = yaml_perms - db_perms
        extra_in_db = db_perms - yaml_perms - {"*"}
        if missing_in_db:
            errors.append(f"permissions in YAML missing from DB: {sorted(missing_in_db)}")
        if extra_in_db:
            errors.append(f"permissions in DB not in YAML: {sorted(extra_in_db)}")

        cur.execute(
            """
            SELECT r.name, p.name
            FROM roles r
            JOIN role_permissions rp ON rp.role_id = r.id
            JOIN permissions p ON p.id = rp.permission_id
            ORDER BY r.name, p.name
            """
        )
        db_grants: dict[str, set[str]] = {}
        for role_name, perm_name in cur.fetchall():
            db_grants.setdefault(role_name, set()).add(perm_name)

        for role_name, expected in yaml_roles.items():
            if role_name == "PLATFORM_SUPER_ADMIN":
                continue
            actual = db_grants.get(role_name, set())
            missing = expected - actual
            if missing:
                errors.append(
                    f"role {role_name} missing DB grants: {sorted(missing)}"
                )
            extra = actual - expected
            if extra:
                errors.append(
                    f"role {role_name} has extra DB grants not in YAML: {sorted(extra)}"
                )

    if errors:
        print("Permission DB parity FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("Permission DB parity OK (YAML ↔ PostgreSQL).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
