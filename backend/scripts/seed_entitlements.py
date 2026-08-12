#!/usr/bin/env python3
"""Seed EntitlementDefinition, MembershipEntitlement, and EntitlementWallet for DEMO-001."""

import asyncio
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.entitlement import (
    EntitlementDefinition,
    EntitlementType,
    EntitlementWallet,
    MembershipEntitlement,
    MembershipEntitlementStatus,
)
from app.models.member import Member
from app.models.membership import Membership
from app.models.tenant import Tenant
from scripts.seed_demo_tenant import DEMO_MEMBER_NUMBER, _engine_url


async def seed_entitlements():
    url = _engine_url()
    engine = create_async_engine(url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        res_tenant = await session.execute(select(Tenant).order_by(Tenant.created_at))
        tenant = res_tenant.scalars().first()
        if not tenant:
            return

        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant.id)},
        )

        res_ed = await session.execute(
            select(EntitlementDefinition).where(
                EntitlementDefinition.tenant_id == tenant.id,
                EntitlementDefinition.code == "GYM_ENTRY",
            )
        )
        ed = res_ed.scalars().first()
        if not ed:
            ed = EntitlementDefinition(
                tenant_id=tenant.id,
                code="GYM_ENTRY",
                name="Gym Entry Access",
                type=EntitlementType.BOOLEAN,
                is_active=True,
            )
            session.add(ed)
            await session.flush()

        res_member = await session.execute(
            select(Member).where(
                Member.tenant_id == tenant.id,
                Member.member_number == DEMO_MEMBER_NUMBER,
            )
        )
        member = res_member.scalars().first()

        res_ms = await session.execute(
            select(Membership).where(
                Membership.tenant_id == tenant.id,
                Membership.member_id == member.id,
                Membership.status == "ACTIVE",
            )
        )
        ms = res_ms.scalars().first()

        if member and ms:
            res_me = await session.execute(
                select(MembershipEntitlement).where(
                    MembershipEntitlement.tenant_id == tenant.id,
                    MembershipEntitlement.membership_id == ms.id,
                    MembershipEntitlement.entitlement_id == ed.id,
                )
            )
            me = res_me.scalars().first()
            if not me:
                me = MembershipEntitlement(
                    tenant_id=tenant.id,
                    membership_id=ms.id,
                    entitlement_id=ed.id,
                    granted_quantity=1,
                    status=MembershipEntitlementStatus.ACTIVE.value,
                )
                session.add(me)
                await session.flush()

            res_wallet = await session.execute(
                select(EntitlementWallet).where(
                    EntitlementWallet.tenant_id == tenant.id,
                    EntitlementWallet.member_id == member.id,
                    EntitlementWallet.entitlement_id == ed.id,
                )
            )
            wallet = res_wallet.scalars().first()
            if not wallet:
                wallet = EntitlementWallet(
                    tenant_id=tenant.id,
                    member_id=member.id,
                    membership_id=ms.id,
                    membership_entitlement_id=me.id,
                    entitlement_id=ed.id,
                    allocated=1,
                    consumed=0,
                    reserved=0,
                    remaining=1,
                )
                session.add(wallet)
                await session.flush()
                print(f"Created EntitlementWallet for member {member.id}")

        await session.commit()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_entitlements())
