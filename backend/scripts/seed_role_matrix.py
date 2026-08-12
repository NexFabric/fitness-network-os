#!/usr/bin/env python3
"""Seed one login user per portal role, in a single shared tenant.

Backs the role-isolation e2e suite: every portal needs a real principal to log
in as, and the trainer portal additionally needs a member assigned to it so the
assignment scope has something to show.

Idempotent — re-running refreshes password hashes and re-asserts assignments.

    ENVIRONMENT=... uv run python scripts/seed_role_matrix.py

Prints the credentials as JSON so the e2e runner can consume them.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASSWORD = "E2ePortal123!"  # local seed fixture, never a real secret

ORG_NAME = "E2E Federation"
TENANT_NAME = "E2E Club"
TENANT_CODE = "E2E-001"

# email suffix → role name. MEMBER and TRAINER both need member rows.
ROLE_USERS: dict[str, str] = {
    "owner": "GYM_OWNER",
    "trainer": "TRAINER",
    "member": "MEMBER",
    "analyst": "FEDERATION_ANALYST",
}


def _engine_url() -> str:
    from app.core.config import settings

    return os.environ.get("MIGRATOR_DATABASE_URL") or str(
        settings.MIGRATOR_DATABASE_URL
    )


async def _set_tenant_rls(session, tenant_id: UUID) -> None:
    from sqlalchemy import text

    from app.api.deps import current_tenant_id_var

    current_tenant_id_var.set(tenant_id)
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )


async def _seed_access_rights(session, tenant_id: UUID, member_id: UUID) -> None:
    """Give the member an active membership and a GYM_ENTRY wallet with balance."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import select

    from app.models.entitlement import (
        EntitlementDefinition,
        EntitlementType,
        EntitlementWallet,
        MembershipEntitlement,
        MembershipEntitlementStatus,
    )
    from app.models.membership import Membership, Plan, PlanVersion

    plan = (
        await session.execute(
            select(Plan).where(Plan.tenant_id == tenant_id, Plan.name == "E2E Plan")
        )
    ).scalar_one_or_none()
    if plan is None:
        plan = Plan(tenant_id=tenant_id, name="E2E Plan", is_active=True)
        session.add(plan)
        await session.flush()

    version = (
        await session.execute(
            select(PlanVersion).where(
                PlanVersion.tenant_id == tenant_id, PlanVersion.plan_id == plan.id
            )
        )
    ).scalar_one_or_none()
    if version is None:
        version = PlanVersion(
            tenant_id=tenant_id,
            plan_id=plan.id,
            version=1,
            price_amount_minor=10000,
            currency="TRY",
            billing_cycle_months=12,
            is_published=True,
        )
        session.add(version)
        await session.flush()

    now = datetime.now(UTC)
    membership = (
        await session.execute(
            select(Membership).where(
                Membership.tenant_id == tenant_id,
                Membership.member_id == member_id,
                Membership.status == "ACTIVE",
            )
        )
    ).scalar_one_or_none()
    if membership is None:
        membership = Membership(
            tenant_id=tenant_id,
            member_id=member_id,
            plan_version_id=version.id,
            status="ACTIVE",
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=365),
        )
        session.add(membership)
        await session.flush()

    definition = (
        await session.execute(
            select(EntitlementDefinition).where(
                EntitlementDefinition.tenant_id == tenant_id,
                EntitlementDefinition.code == "GYM_ENTRY",
            )
        )
    ).scalar_one_or_none()
    if definition is None:
        definition = EntitlementDefinition(
            tenant_id=tenant_id,
            code="GYM_ENTRY",
            name="Gym Entry Access",
            type=EntitlementType.BOOLEAN,
            is_active=True,
        )
        session.add(definition)
        await session.flush()

    link = (
        await session.execute(
            select(MembershipEntitlement).where(
                MembershipEntitlement.tenant_id == tenant_id,
                MembershipEntitlement.membership_id == membership.id,
                MembershipEntitlement.entitlement_id == definition.id,
            )
        )
    ).scalar_one_or_none()
    if link is None:
        link = MembershipEntitlement(
            tenant_id=tenant_id,
            membership_id=membership.id,
            entitlement_id=definition.id,
            granted_quantity=1000,
            status=MembershipEntitlementStatus.ACTIVE.value,
        )
        session.add(link)
        await session.flush()

    wallet = (
        await session.execute(
            select(EntitlementWallet).where(
                EntitlementWallet.tenant_id == tenant_id,
                EntitlementWallet.member_id == member_id,
                EntitlementWallet.entitlement_id == definition.id,
            )
        )
    ).scalar_one_or_none()
    if wallet is None:
        session.add(
            EntitlementWallet(
                tenant_id=tenant_id,
                member_id=member_id,
                membership_id=membership.id,
                membership_entitlement_id=link.id,
                entitlement_id=definition.id,
                allocated=1000,
                consumed=0,
                reserved=0,
                remaining=1000,
            )
        )
        await session.flush()
    else:
        # Re-running the seed must not leave a drained wallet behind.
        wallet.allocated = 1000
        wallet.consumed = 0
        wallet.reserved = 0
        wallet.remaining = 1000
        await session.flush()


async def seed() -> dict[str, object]:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from app.core.security import get_password_hash
    from app.models.member import Member
    from app.models.organization import Organization
    from app.models.rbac import Role, UserRole
    from app.models.tenant import Tenant
    from app.models.trainer_assignment import TrainerAssignment
    from app.models.user import User

    engine = create_async_engine(_engine_url(), pool_pre_ping=True, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with Session() as session:
            org = (
                await session.execute(
                    select(Organization).where(Organization.name == ORG_NAME)
                )
            ).scalar_one_or_none()
            if org is None:
                org = Organization(name=ORG_NAME, domain="e2e.local")
                session.add(org)
                await session.flush()

            tenant = (
                await session.execute(
                    select(Tenant).where(Tenant.location_code == TENANT_CODE)
                )
            ).scalar_one_or_none()
            if tenant is None:
                tenant = Tenant(
                    name=TENANT_NAME,
                    organization_id=org.id,
                    location_code=TENANT_CODE,
                )
                session.add(tenant)
                await session.flush()

            users: dict[str, dict[str, str]] = {}
            for suffix, role_name in ROLE_USERS.items():
                role = (
                    await session.execute(select(Role).where(Role.name == role_name))
                ).scalar_one_or_none()
                if role is None:
                    raise SystemExit(
                        f"Role {role_name!r} missing. Run: alembic upgrade head"
                    )

                email = f"e2e.{suffix}@e2e.local"
                user = (
                    await session.execute(select(User).where(User.email == email))
                ).scalar_one_or_none()
                if user is None:
                    user = User(
                        email=email,
                        hashed_password=get_password_hash(PASSWORD),
                        is_active=True,
                        is_superuser=False,
                    )
                    session.add(user)
                    await session.flush()
                else:
                    user.hashed_password = get_password_hash(PASSWORD)
                    user.is_active = True
                    await session.flush()

                # Federation roles attach to the organization, not the tenant —
                # that is what get_federation_scope reads.
                is_federation = role_name.startswith("FEDERATION")
                scope_tenant = None if is_federation else tenant.id
                scope_org = org.id if is_federation else None

                existing = (
                    await session.execute(
                        select(UserRole).where(
                            UserRole.user_id == user.id,
                            UserRole.role_id == role.id,
                        )
                    )
                ).scalar_one_or_none()
                if existing is None:
                    session.add(
                        UserRole(
                            user_id=user.id,
                            role_id=role.id,
                            tenant_id=scope_tenant,
                            organization_id=scope_org,
                        )
                    )
                    await session.flush()

                users[suffix] = {
                    "email": email,
                    "password": PASSWORD,
                    "role": role_name,
                    "user_id": str(user.id),
                }

            await _set_tenant_rls(session, tenant.id)

            # Member row bound to the MEMBER user so /me/* resolves.
            member_user_id = UUID(users["member"]["user_id"])
            member = (
                await session.execute(
                    select(Member).where(
                        Member.tenant_id == tenant.id,
                        Member.member_number == "E2E-M-001",
                    )
                )
            ).scalar_one_or_none()
            if member is None:
                member = Member(
                    tenant_id=tenant.id,
                    member_number="E2E-M-001",
                    first_name="E2E",
                    last_name="Sporcu",
                    email=users["member"]["email"],
                    status="ACTIVE",
                    user_id=member_user_id,
                )
                session.add(member)
                await session.flush()
            else:
                member.user_id = member_user_id
                member.status = "ACTIVE"
                await session.flush()

            # A second member the trainer is NOT assigned to, so the isolation
            # test has something that must stay invisible.
            unassigned = (
                await session.execute(
                    select(Member).where(
                        Member.tenant_id == tenant.id,
                        Member.member_number == "E2E-M-002",
                    )
                )
            ).scalar_one_or_none()
            if unassigned is None:
                unassigned = Member(
                    tenant_id=tenant.id,
                    member_number="E2E-M-002",
                    first_name="Atanmamis",
                    last_name="Uye",
                    status="ACTIVE",
                )
                session.add(unassigned)
                await session.flush()

            trainer_user_id = UUID(users["trainer"]["user_id"])
            assignment = (
                await session.execute(
                    select(TrainerAssignment).where(
                        TrainerAssignment.tenant_id == tenant.id,
                        TrainerAssignment.trainer_user_id == trainer_user_id,
                        TrainerAssignment.member_id == member.id,
                    )
                )
            ).scalar_one_or_none()
            if assignment is None:
                session.add(
                    TrainerAssignment(
                        tenant_id=tenant.id,
                        trainer_user_id=trainer_user_id,
                        member_id=member.id,
                        is_active=True,
                    )
                )
            else:
                assignment.is_active = True

            # Active membership + entitlement wallet, so a QR issued by the
            # member portal is actually GRANTED at the turnstile. Without these
            # the happy path would deny and the e2e round-trip would be
            # testing the denial branch by accident.
            await _seed_access_rights(session, tenant.id, member.id)

            await session.commit()

            return {
                "tenant_id": str(tenant.id),
                "organization_id": str(org.id),
                "assigned_member_id": str(member.id),
                "unassigned_member_id": str(unassigned.id),
                "users": users,
            }
    finally:
        await engine.dispose()


def main() -> int:
    result = asyncio.run(seed())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
