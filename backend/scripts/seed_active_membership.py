#!/usr/bin/env python3
"""Seed an active Membership for DEMO-001 so scanner QR checkins return GRANTED (green screen)."""

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.member import Member
from app.models.membership import Membership, Plan, PlanVersion
from app.models.tenant import Tenant
from scripts.seed_demo_tenant import _engine_url, DEMO_MEMBER_NUMBER

async def seed_active_membership():
    url = _engine_url()
    engine = create_async_engine(url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Find tenant
        res_tenant = await session.execute(select(Tenant).order_by(Tenant.created_at))
        tenant = res_tenant.scalars().first()
        if not tenant:
            print("No tenant found. Run seed_demo.py first.")
            return

        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant.id)},
        )

        # Find demo member
        res_member = await session.execute(
            select(Member).where(
                Member.tenant_id == tenant.id,
                Member.member_number == DEMO_MEMBER_NUMBER,
            )
        )
        member = res_member.scalars().first()
        if not member:
            print("No DEMO-001 member found. Run seed_demo.py first.")
            return

        # Find or create Plan & PlanVersion
        res_plan = await session.execute(
            select(Plan).where(Plan.tenant_id == tenant.id)
        )
        plan = res_plan.scalars().first()
        if not plan:
            plan = Plan(
                tenant_id=tenant.id,
                name="Demo VIP Plan",
                is_active=True,
            )
            session.add(plan)
            await session.flush()

        res_pv = await session.execute(
            select(PlanVersion).where(PlanVersion.tenant_id == tenant.id, PlanVersion.plan_id == plan.id)
        )
        pv = res_pv.scalars().first()
        if not pv:
            pv = PlanVersion(
                tenant_id=tenant.id,
                plan_id=plan.id,
                version=1,
                price_amount_minor=10000,
                currency="TRY",
                billing_cycle_months=12,
                is_published=True,
            )
            session.add(pv)
            await session.flush()

        # Check existing membership
        res_ms = await session.execute(
            select(Membership).where(
                Membership.tenant_id == tenant.id,
                Membership.member_id == member.id,
                Membership.status == "ACTIVE",
            )
        )
        ms = res_ms.scalars().first()
        now = datetime.now(UTC)
        if not ms:
            ms = Membership(
                tenant_id=tenant.id,
                member_id=member.id,
                plan_version_id=pv.id,
                status="ACTIVE",
                start_date=now - timedelta(days=1),
                end_date=now + timedelta(days=365),
            )
            session.add(ms)
            await session.flush()
            print(f"Created active membership {ms.id} for member {member.id}")
        else:
            print(f"Active membership {ms.id} already exists for member {member.id}")

        await session.commit()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_active_membership())
