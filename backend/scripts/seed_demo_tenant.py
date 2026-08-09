#!/usr/bin/env python3
"""Seed a demo Organization + Tenant + GYM_OWNER user + session for Admin Web.

Idempotent: re-running refreshes the password hash and issues a new
session token (previous demo session rows for this user are revoked).

Also seeds a sample Location + Member so Admin Members/Locations lists
are non-empty after login.

Prerequisites
-------------
- Postgres up (``docker compose up -d``)
- Migrations applied: ``cd backend && alembic upgrade head``
- ``.env`` with ``DATABASE_URL`` / ``MIGRATOR_DATABASE_URL`` (migrator preferred)

Usage (from ``backend/``)::

    set -a && source .env && set +a
    uv run python scripts/seed_demo_tenant.py
    # alias:
    uv run python scripts/seed_demo.py

    # optional flags
    uv run python scripts/seed_demo_tenant.py --role GYM_ADMIN --no-member
    uv run python scripts/seed_demo_tenant.py --email admin@demo.local --password 'ChangeMe!'

Prints on stdout (copy into Admin login at http://localhost:5173/login)::

    === Demo seed ready ===
    tenant_id:      <uuid>
    email:          demo.admin@demo.local
    password:       DemoAdmin123!
    role:           GYM_OWNER
    bearer_token:   <raw session token — paste without Bearer prefix>
    member_id:      <uuid or (none)>
    location_id:    <uuid or (none)>
    Authorization:  Bearer <raw>
    X-Tenant-ID:    <uuid>

Admin Web login only needs **Session token** + **Tenant ID**.
Not production-ready — local/dev credentials only.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

# Allow ``uv run python scripts/...`` without package install path hacks.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Stable demo identifiers (idempotent lookup keys)
DEMO_ORG_DOMAIN = "demo.local"
DEMO_ORG_NAME = "Demo Organization"
DEMO_TENANT_LOCATION_CODE = "DEMO-MAIN"
DEMO_TENANT_NAME = "Demo Gym"
DEMO_EMAIL = "demo.admin@demo.local"
DEMO_PASSWORD = "DemoAdmin123!"
DEMO_MEMBER_NUMBER = "DEMO-001"
DEMO_LOCATION_NAME = "Demo Main Floor"
DEFAULT_ROLE = "GYM_OWNER"
SESSION_DAYS = 30


def _engine_url() -> str:
    """Prefer migrator (schema owner / superuser); fall back to app DATABASE_URL."""
    import os

    from app.core.config import settings

    url = (
        os.environ.get("MIGRATOR_DATABASE_URL")
        or str(settings.MIGRATOR_DATABASE_URL)
        or os.environ.get("DATABASE_URL")
        or str(settings.DATABASE_URL)
    )
    if not url:
        raise SystemExit(
            "MIGRATOR_DATABASE_URL or DATABASE_URL required (load backend/.env)"
        )
    return str(url)


async def _set_tenant_rls(session, tenant_id: UUID) -> None:
    """FORCE RLS on members requires app.current_tenant_id even for table owner."""
    from sqlalchemy import text

    from app.api.deps import current_tenant_id_var

    current_tenant_id_var.set(tenant_id)
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )


async def seed_demo(
    *,
    email: str = DEMO_EMAIL,
    password: str = DEMO_PASSWORD,
    role_name: str = DEFAULT_ROLE,
    with_member: bool = True,
    with_location: bool = True,
) -> dict[str, str | None]:
    """Create or update demo tenant + owner user; return printable credentials."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.orm import selectinload

    from app.core.security import generate_session_token, get_password_hash
    from app.models.location import Location
    from app.models.member import Member
    from app.models.organization import Organization
    from app.models.rbac import Role, UserRole
    from app.models.tenant import Tenant
    from app.models.user import User, UserSession

    engine = create_async_engine(_engine_url(), pool_pre_ping=True, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with Session() as session:
            # --- Organization ---
            org = (
                await session.execute(
                    select(Organization).where(Organization.domain == DEMO_ORG_DOMAIN)
                )
            ).scalar_one_or_none()
            if org is None:
                org = Organization(name=DEMO_ORG_NAME, domain=DEMO_ORG_DOMAIN)
                session.add(org)
                await session.flush()

            # --- Tenant (Gym) ---
            tenant = (
                await session.execute(
                    select(Tenant).where(
                        Tenant.location_code == DEMO_TENANT_LOCATION_CODE
                    )
                )
            ).scalar_one_or_none()
            if tenant is None:
                tenant = Tenant(
                    name=DEMO_TENANT_NAME,
                    organization_id=org.id,
                    location_code=DEMO_TENANT_LOCATION_CODE,
                )
                session.add(tenant)
                await session.flush()

            # --- Canonical system role (seeded by migrations / permissions.yml) ---
            role = (
                await session.execute(
                    select(Role)
                    .options(selectinload(Role.permissions))
                    .where(Role.name == role_name)
                )
            ).scalar_one_or_none()
            if role is None:
                raise SystemExit(
                    f"Role {role_name!r} not found. Run: alembic upgrade head "
                    f"(RBAC seed migrations must be applied)."
                )
            perm_count = len(role.permissions)
            if perm_count == 0:
                raise SystemExit(
                    f"Role {role_name!r} has zero permissions in DB. "
                    "Run alembic upgrade head and scripts/check_permissions_db.py."
                )

            # --- User (hashed password via app.core.security argon2) ---
            user = (
                await session.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
            if user is None:
                user = User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    is_active=True,
                    is_superuser=False,
                )
                session.add(user)
                await session.flush()
            else:
                user.hashed_password = get_password_hash(password)
                user.is_active = True
                await session.flush()

            # --- UserRole scoped to tenant ---
            existing_ur = (
                await session.execute(
                    select(UserRole).where(
                        UserRole.user_id == user.id,
                        UserRole.role_id == role.id,
                        UserRole.tenant_id == tenant.id,
                    )
                )
            ).scalar_one_or_none()
            if existing_ur is None:
                session.add(
                    UserRole(
                        user_id=user.id,
                        role_id=role.id,
                        tenant_id=tenant.id,
                        organization_id=None,
                    )
                )
                await session.flush()

            # --- Session: revoke prior demo sessions, mint new raw token ---
            prior = (
                await session.execute(
                    select(UserSession).where(
                        UserSession.user_id == user.id,
                        UserSession.is_revoked.is_(False),
                    )
                )
            ).scalars().all()
            for s in prior:
                s.is_revoked = True

            raw_token, token_hash = generate_session_token()
            session.add(
                UserSession(
                    user_id=user.id,
                    token_hash=token_hash,
                    expires_at=datetime.now(UTC) + timedelta(days=SESSION_DAYS),
                    is_revoked=False,
                    user_agent="seed_demo_tenant",
                )
            )
            await session.flush()

            # Tenant-owned tables need GUC even when connected as migrator
            # if FORCE ROW LEVEL SECURITY is enabled.
            await _set_tenant_rls(session, tenant.id)

            # --- Optional sample Location (Admin Locations page) ---
            location_id: str | None = None
            if with_location:
                loc = (
                    await session.execute(
                        select(Location).where(
                            Location.tenant_id == tenant.id,
                            Location.name == DEMO_LOCATION_NAME,
                        )
                    )
                ).scalar_one_or_none()
                if loc is None:
                    loc = Location(
                        tenant_id=tenant.id,
                        name=DEMO_LOCATION_NAME,
                        timezone="Europe/Istanbul",
                        address="Demo St 1",
                    )
                    session.add(loc)
                    await session.flush()
                location_id = str(loc.id)

            # --- Optional Member bound to user (for /me + Admin Members) ---
            member_id: str | None = None
            if with_member:
                member = (
                    await session.execute(
                        select(Member).where(
                            Member.tenant_id == tenant.id,
                            Member.member_number == DEMO_MEMBER_NUMBER,
                        )
                    )
                ).scalar_one_or_none()
                if member is None:
                    member = Member(
                        tenant_id=tenant.id,
                        member_number=DEMO_MEMBER_NUMBER,
                        first_name="Demo",
                        last_name="Owner",
                        email=email,
                        status="ACTIVE",
                        user_id=user.id,
                    )
                    session.add(member)
                    await session.flush()
                else:
                    member.user_id = user.id
                    member.email = email
                    member.status = "ACTIVE"
                    await session.flush()
                member_id = str(member.id)

            await session.commit()

            return {
                "tenant_id": str(tenant.id),
                "organization_id": str(org.id),
                "user_id": str(user.id),
                "email": email,
                "password": password,
                "role": role_name,
                "role_permission_count": str(perm_count),
                "bearer_token": raw_token,
                "member_id": member_id,
                "location_id": location_id,
            }
    finally:
        await engine.dispose()


def _print_result(result: dict[str, str | None]) -> None:
    token = result["bearer_token"] or ""
    tenant_id = result["tenant_id"] or ""
    print("=== Demo seed ready (local/dev only — not production) ===")
    print(f"tenant_id:      {tenant_id}")
    print(f"organization_id:{result['organization_id']}")
    print(f"user_id:        {result['user_id']}")
    print(f"email:          {result['email']}")
    print(f"password:       {result['password']}  (hashed; Admin uses token paste)")
    print(f"role:           {result['role']} ({result['role_permission_count']} perms)")
    print(f"bearer_token:   {token}")
    print(f"member_id:      {result['member_id'] or '(none)'}")
    print(f"location_id:    {result.get('location_id') or '(none)'}")
    print(f"Authorization:  Bearer {token}")
    print(f"X-Tenant-ID:    {tenant_id}")
    print()
    print("Admin Web → http://localhost:5173/login")
    print("  Session token  = bearer_token (no 'Bearer ' prefix)")
    print("  Tenant ID      = tenant_id")
    print()
    print(
        f'curl -sS -H "Authorization: Bearer {token}" '
        f'-H "X-Tenant-ID: {tenant_id}" http://localhost:8000/api/v1/members'
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed demo tenant + GYM_OWNER session for local Admin Web."
    )
    parser.add_argument(
        "--email",
        default=DEMO_EMAIL,
        help=f"Admin email (default: {DEMO_EMAIL})",
    )
    parser.add_argument(
        "--password",
        default=DEMO_PASSWORD,
        help="Plain password (hashed with argon2 before store)",
    )
    parser.add_argument(
        "--role",
        default=DEFAULT_ROLE,
        choices=["GYM_ADMIN", "GYM_OWNER", "GYM_MANAGER"],
        help=f"System role name from DB (default: {DEFAULT_ROLE})",
    )
    parser.add_argument(
        "--no-member",
        action="store_true",
        help="Skip creating a Member bound to the demo user",
    )
    args = parser.parse_args(argv)

    result = asyncio.run(
        seed_demo(
            email=args.email,
            password=args.password,
            role_name=args.role,
            with_member=not args.no_member,
        )
    )
    _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
