"""
Real PostgreSQL Phase 11 EXPAND migration test.

Flow:
  clean schema → alembic upgrade e6f7a8b9c0d1 (pre-Phase11)
  → seed legacy Float rows via SQL
  → alembic upgrade f7a8b9c0d1e2 (EXPAND)
  → SELECT new columns from PostgreSQL and reconcile
  → assert legacy float columns still exist
  → restore alembic head for other tests
"""

from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

PRE_PHASE11 = "e6f7a8b9c0d1"
PHASE11_EXPAND = "f7a8b9c0d1e2"

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/fitness_test_db",
)
SYNC_URL = TEST_DATABASE_URL.replace("+asyncpg", "")


def _env() -> dict[str, str]:
    env = os.environ.copy()
    parsed = urlparse(TEST_DATABASE_URL)
    if parsed.password:
        env["PGPASSWORD"] = parsed.password
    env["DATABASE_URL"] = TEST_DATABASE_URL
    env["MIGRATOR_DATABASE_URL"] = TEST_DATABASE_URL
    return env


def _psql(sql: str) -> None:
    env = _env()
    subprocess.run(
        ["psql", SYNC_URL, "-v", "ON_ERROR_STOP=1", "-c", sql],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _alembic(revision: str) -> None:
    env = _env()
    backend = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    subprocess.run(
        ["uv", "run", "alembic", "upgrade", revision],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        cwd=backend,
    )


def _expected_minor_from_seed(value: float | None) -> int | None:
    if value is None:
        return None
    return int(
        (Decimal(str(value)) * Decimal(100)).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
    )


def _expected_bps(prob: float | None) -> int | None:
    if prob is None:
        return None
    bps = int(
        (Decimal(str(prob)) * Decimal(10000)).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
    )
    return max(0, min(10000, bps))


@pytest.mark.asyncio
async def test_phase11_expand_migration_from_legacy_float_rows():
    """Seed pre-Phase11 Float columns, upgrade EXPAND, reconcile on real PG."""
    _psql(
        "DROP SCHEMA public CASCADE; CREATE SCHEMA public; "
        "GRANT ALL ON SCHEMA public TO CURRENT_USER; "
        "GRANT ALL ON SCHEMA public TO public;"
    )
    _alembic(PRE_PHASE11)

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    tenant_id = uuid4()
    org_id = uuid4()
    member_id = uuid4()
    now = datetime.now(UTC)

    opp_cases = [
        (uuid4(), None),
        (uuid4(), 0.0),
        (uuid4(), 19.99),
        (uuid4(), 19.995),
        (uuid4(), 1000.50),
        (uuid4(), 999999.99),
    ]
    ret_cases = [
        (uuid4(), 0.0),
        (uuid4(), 0.125),
        (uuid4(), 1.0),
    ]

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                INSERT INTO organizations (id, name, domain, created_at, updated_at)
                VALUES (:id, 'Mig Org', :domain, :now, :now)
                """
            ),
            {
                "id": org_id,
                "domain": f"mig-{uuid4().hex[:8]}.test",
                "now": now,
            },
        )
        await conn.execute(
            text(
                """
                INSERT INTO tenants (
                    id, name, organization_id, location_code, created_at, updated_at
                )
                VALUES (:id, 'Mig Tenant', :org, :loc, :now, :now)
                """
            ),
            {
                "id": tenant_id,
                "org": org_id,
                "loc": f"LOC-{uuid4().hex[:6]}",
                "now": now,
            },
        )
        await conn.execute(
            text(
                """
                INSERT INTO members (
                    id, tenant_id, member_number, first_name, last_name, email, status,
                    created_at, updated_at
                )
                VALUES (
                    :id, :tenant, :num, 'Mig', 'Member', :email, 'ACTIVE', :now, :now
                )
                """
            ),
            {
                "id": member_id,
                "tenant": tenant_id,
                "num": f"M-{uuid4().hex[:6]}",
                "email": f"mig-{uuid4().hex[:6]}@test.com",
                "now": now,
            },
        )

        for oid, val in opp_cases:
            await conn.execute(
                text(
                    """
                    INSERT INTO opportunities (
                        id, tenant_id, lead_id, member_id, stage, value, probability,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :tenant, NULL, NULL, 'PROSPECTING', :value, NULL, :now, :now
                    )
                    """
                ),
                {"id": oid, "tenant": tenant_id, "value": val, "now": now},
            )

        for i, (rid, prob) in enumerate(ret_cases):
            mid = member_id if i == 0 else uuid4()
            if i > 0:
                await conn.execute(
                    text(
                        """
                        INSERT INTO members (
                            id, tenant_id, member_number, first_name, last_name, email,
                            status, created_at, updated_at
                        )
                        VALUES (
                            :id, :tenant, :num, 'Mig', :ln, :email, 'ACTIVE', :now, :now
                        )
                        """
                    ),
                    {
                        "id": mid,
                        "tenant": tenant_id,
                        "num": f"M-{uuid4().hex[:6]}",
                        "ln": f"R{i}",
                        "email": f"mig-r{i}-{uuid4().hex[:4]}@test.com",
                        "now": now,
                    },
                )
            await conn.execute(
                text(
                    """
                    INSERT INTO retention_cockpit (
                        id, tenant_id, member_id, health_score, churn_probability,
                        last_calculated_at, risk_level, created_at, updated_at
                    )
                    VALUES (
                        :id, :tenant, :member, 50, :prob, :now, 'MED', :now, :now
                    )
                    """
                ),
                {
                    "id": rid,
                    "tenant": tenant_id,
                    "member": mid,
                    "prob": prob,
                    "now": now,
                },
            )

        pre_opp = (
            await conn.execute(
                text("SELECT COUNT(*) FROM opportunities WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
        ).scalar_one()
        pre_ret = (
            await conn.execute(
                text("SELECT COUNT(*) FROM retention_cockpit WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
        ).scalar_one()

    assert pre_opp == len(opp_cases)
    assert pre_ret == len(ret_cases)

    _alembic(PHASE11_EXPAND)

    async with engine.begin() as conn:
        opp_cols = {
            r[0]
            for r in (
                await conn.execute(
                    text(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = 'opportunities'
                        """
                    )
                )
            ).fetchall()
        }
        ret_cols = {
            r[0]
            for r in (
                await conn.execute(
                    text(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = 'retention_cockpit'
                        """
                    )
                )
            ).fetchall()
        }
        assert "value" in opp_cols
        assert "value_amount_minor" in opp_cols
        assert "currency" in opp_cols
        assert "churn_probability" in ret_cols
        assert "churn_probability_bps" in ret_cols

        post_opp = (
            await conn.execute(
                text("SELECT COUNT(*) FROM opportunities WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
        ).scalar_one()
        post_ret = (
            await conn.execute(
                text("SELECT COUNT(*) FROM retention_cockpit WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
        ).scalar_one()
        assert post_opp == pre_opp
        assert post_ret == pre_ret

        for oid, val in opp_cases:
            row = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT value, value_amount_minor, currency
                        FROM opportunities WHERE id = :id
                        """
                        ),
                        {"id": oid},
                    )
                )
                .mappings()
                .one()
            )
            expected = _expected_minor_from_seed(val)
            # Allow ±1 minor for float IEEE edge cases on ROUND boundaries
            if expected is None:
                assert row["value_amount_minor"] is None
            else:
                got = row["value_amount_minor"]
                assert got is not None
                assert abs(got - expected) <= 1, (
                    f"opp {oid}: value={val} expected~{expected} got={got}"
                )
            if val is not None:
                assert row["currency"] == "TRY"
            if val is None:
                assert row["value"] is None
            else:
                assert row["value"] is not None

        for rid, prob in ret_cases:
            row = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT churn_probability, churn_probability_bps
                        FROM retention_cockpit WHERE id = :id
                        """
                        ),
                        {"id": rid},
                    )
                )
                .mappings()
                .one()
            )
            expected_bps = _expected_bps(prob)
            assert row["churn_probability_bps"] == expected_bps, (
                f"ret {rid}: prob={prob} expected bps={expected_bps} "
                f"got={row['churn_probability_bps']}"
            )
            assert row["churn_probability"] is not None

        rev = (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one()
        assert rev == PHASE11_EXPAND

    await engine.dispose()

    _alembic("head")
    _psql(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN "
        "CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password' NOSUPERUSER NOBYPASSRLS; "
        "END IF; END $$; "
        "GRANT USAGE ON SCHEMA public TO app_user; "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user; "
        "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO app_user; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user; "
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO app_user;"
    )


@pytest.mark.asyncio
async def test_phase11_expand_schema_guard_after_head(pg_engine):
    """While EXPAND is current: legacy + new columns must coexist after full head."""
    async with pg_engine.connect() as conn:
        opp = (
            await conn.execute(
                text(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'opportunities'
                    """
                )
            )
        ).fetchall()
        ret = (
            await conn.execute(
                text(
                    """
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'retention_cockpit'
                    """
                )
            )
        ).fetchall()
        opp_cols = {r[0] for r in opp}
        ret_cols = {r[0] for r in ret}
        assert "value" in opp_cols
        assert "value_amount_minor" in opp_cols
        assert "currency" in opp_cols
        assert "churn_probability" in ret_cols
        assert "churn_probability_bps" in ret_cols
