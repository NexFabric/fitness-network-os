"""Growth CRM tables are tenant-owned: real PostgreSQL RLS, not SQLite theatre."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.api.deps import current_tenant_id_var
from app.models.growth import Lead


@pytest.mark.asyncio
async def test_growth_leads_rls_isolates_tenants(pg_session_maker):
    tenant_a = uuid4()
    tenant_b = uuid4()

    token_a = current_tenant_id_var.set(tenant_a)
    try:
        async with pg_session_maker() as session:
            session.add(
                Lead(
                    tenant_id=tenant_a,
                    first_name="Ada",
                    last_name="A",
                    status="NEW",
                )
            )
            await session.commit()
    finally:
        current_tenant_id_var.reset(token_a)

    token_b = current_tenant_id_var.set(tenant_b)
    try:
        async with pg_session_maker() as session:
            session.add(
                Lead(
                    tenant_id=tenant_b,
                    first_name="Bora",
                    last_name="B",
                    status="NEW",
                )
            )
            await session.commit()
    finally:
        current_tenant_id_var.reset(token_b)

    token_a = current_tenant_id_var.set(tenant_a)
    try:
        async with pg_session_maker() as session:
            rows = list((await session.execute(select(Lead))).scalars().all())
            assert len(rows) == 1
            assert rows[0].first_name == "Ada"
            assert rows[0].tenant_id == tenant_a
    finally:
        current_tenant_id_var.reset(token_a)

    token_b = current_tenant_id_var.set(tenant_b)
    try:
        async with pg_session_maker() as session:
            rows = list((await session.execute(select(Lead))).scalars().all())
            assert len(rows) == 1
            assert rows[0].first_name == "Bora"
    finally:
        current_tenant_id_var.reset(token_b)

    token_empty = current_tenant_id_var.set(None)
    try:
        async with pg_session_maker() as session:
            # No tenant context → FORCE RLS hides every row.
            rows = list((await session.execute(select(Lead))).scalars().all())
            assert rows == []
    finally:
        current_tenant_id_var.reset(token_empty)

    token_a = current_tenant_id_var.set(tenant_a)
    try:
        async with pg_session_maker() as session:
            session.add(
                Lead(
                    tenant_id=tenant_b,
                    first_name="Spoof",
                    last_name="X",
                    status="NEW",
                )
            )
            try:
                await session.commit()
                raise AssertionError("spoofed insert should violate growth RLS")
            except Exception as exc:
                await session.rollback()
                text_exc = str(exc).lower()
                assert "row-level security" in text_exc
    finally:
        current_tenant_id_var.reset(token_a)
