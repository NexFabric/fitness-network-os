import hashlib
import secrets
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.member import Member
from app.models.organization import Organization
from app.models.rbac import Permission, Role, UserRole
from app.models.tenant import Tenant
from app.models.user import User, UserSession


@pytest.fixture
async def api_client(pg_session_maker):
    async def override_get_db():
        async with pg_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


def _token_pair() -> tuple[str, str]:
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


async def _ensure_perms(db: AsyncSession, names: list[str]) -> list[Permission]:
    out: list[Permission] = []
    for name in names:
        row = (
            await db.execute(select(Permission).where(Permission.name == name))
        ).scalar_one_or_none()
        if row is None:
            row = Permission(name=name, description=name)
            db.add(row)
            await db.flush()
        out.append(row)
    return out


async def _create_admin(db: AsyncSession, tenant_id) -> tuple[User, str]:
    raw, th = _token_pair()
    user = User(
        email=f"admin-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.flush()

    perms_needed = [
        "gym:read",
        "gym:write",
        "members:read",
        "members:write",
    ]
    perms = await _ensure_perms(db, perms_needed)

    role = Role(
        name=f"ADMIN-{uuid4().hex[:8]}",
        description="admin test role",
        permissions=perms,
    )
    db.add(role)
    await db.flush()

    db.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
        )
    )
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=th,
            expires_at=datetime(2099, 1, 1, tzinfo=UTC),
        )
    )
    await db.commit()
    return user, raw


@pytest.mark.asyncio
async def test_csv_import_pipeline_e2e(api_client, pg_engine):
    """CSV upload -> validation preview -> commit -> members created transactionally."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Import Org", domain=f"imp-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Import T",
            organization_id=org.id,
            location_code=f"I-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        _user, token = await _create_admin(db, tenant.id)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant.id),
    }

    # 1. Upload CSV with 2 valid rows and 1 invalid row (missing last_name)
    csv_data = (
        "first_name,last_name,email,phone,member_number\n"
        "Ahmet,Yilmaz,ahmet@test.com,5551112233,MBR-901\n"
        "Ayse,Kaya,ayse@test.com,5552223344,MBR-902\n"
        "Mehmet,,bad-email,5553334455,MBR-903\n"
    )
    upload_resp = await api_client.post(
        "/api/v1/import/upload",
        json={"filename": "members.csv", "csv_content": csv_data},
        headers=headers,
    )
    assert upload_resp.status_code == 201, upload_resp.text
    batch_data = upload_resp.json()
    batch_id = batch_data["id"]

    assert batch_data["total_rows"] == 3
    assert batch_data["valid_rows"] == 2
    assert batch_data["invalid_rows"] == 1
    assert batch_data["status"] == "PREVIEW"

    # 2. Get batch detail
    detail_resp = await api_client.get(
        f"/api/v1/import/batch/{batch_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    rows = detail_resp.json()["rows"]
    assert len(rows) == 3
    # Row 3 should be invalid
    assert rows[2]["status"] == "INVALID"
    assert "Soyisim" in rows[2]["error_message"]

    # 3. Commit valid rows
    commit_resp = await api_client.post(
        f"/api/v1/import/batch/{batch_id}/commit",
        headers=headers,
    )
    assert commit_resp.status_code == 200
    committed = commit_resp.json()
    assert committed["status"] == "COMPLETED"
    assert committed["imported_rows"] == 2

    # 4. Verify members created in DB
    async with maker() as db:
        res = await db.execute(select(Member).where(Member.tenant_id == tenant.id))
        members = list(res.scalars().all())
        assert len(members) == 2
        names = {m.first_name for m in members}
        assert "Ahmet" in names
        assert "Ayse" in names


@pytest.mark.asyncio
async def test_csv_upload_rejects_formula_prefix_and_oversize(
    api_client, pg_engine
):
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Imp2 Org", domain=f"imp2-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Imp2 T",
            organization_id=org.id,
            location_code=f"I2-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()
        _user, token = await _create_admin(db, tenant.id)
        await db.commit()

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant.id),
    }
    formula = (
        "first_name,last_name,email\n"
        "=cmd|' /C calc',Yilmaz,ahmet@test.com\n"
    )
    preview = await api_client.post(
        "/api/v1/import/upload",
        json={"filename": "evil.csv", "csv_content": formula},
        headers=headers,
    )
    assert preview.status_code == 201, preview.text
    rows = (
        await api_client.get(
            f"/api/v1/import/batch/{preview.json()['id']}", headers=headers
        )
    ).json()["rows"]
    assert rows[0]["status"] == "INVALID"
    assert "formül" in rows[0]["error_message"]

    huge = "first_name,last_name\n" + ("A,B\n" * 5001)
    over = await api_client.post(
        "/api/v1/import/upload",
        json={"filename": "huge.csv", "csv_content": huge},
        headers=headers,
    )
    assert over.status_code == 400
    assert "satır" in over.json()["detail"]


@pytest.mark.asyncio
async def test_tenant_onboarding_state_machine(api_client, pg_engine):
    """Tenant onboarding state transitions and persistence."""
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        org = Organization(name="Onb Org", domain=f"onb-{uuid4().hex[:6]}.com")
        db.add(org)
        await db.flush()
        tenant = Tenant(
            id=uuid4(),
            name="Onb T",
            organization_id=org.id,
            location_code=f"O-{uuid4().hex[:6]}",
        )
        db.add(tenant)
        await db.flush()

        _user, token = await _create_admin(db, tenant.id)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant.id),
    }

    # 1. Initial status -> auto-creates ORG_CREATED
    status_resp = await api_client.get("/api/v1/onboarding/status", headers=headers)
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["current_stage"] == "ORG_CREATED"
    assert data["is_completed"] is False

    # 2. Advance without Location should fail with 400
    adv_fail = await api_client.post(
        "/api/v1/onboarding/advance",
        headers=headers,
        json={
            "next_stage": "PLANS_DEFINED",
            "stage_data": {"plans_count": 3},
        },
    )
    assert adv_fail.status_code == 400
    assert "şube" in adv_fail.json()["detail"].lower()

    # Create Location and published PlanVersion in DB
    from app.models.location import Location
    from app.models.membership import Plan, PlanVersion

    async with maker() as db:
        loc = Location(id=uuid4(), tenant_id=tenant.id, name="Merkez Şube")
        db.add(loc)
        plan = Plan(id=uuid4(), tenant_id=tenant.id, name="Standart Üyelik")
        db.add(plan)
        pv = PlanVersion(
            id=uuid4(),
            tenant_id=tenant.id,
            plan_id=plan.id,
            version=1,
            price_amount_minor=100000,
            currency="TRY",
            billing_cycle_months=1,
            is_published=True,
        )
        db.add(pv)
        await db.commit()

    # 3. Advance to PLANS_DEFINED with step metadata
    adv_resp = await api_client.post(
        "/api/v1/onboarding/advance",
        headers=headers,
        json={
            "next_stage": "PLANS_DEFINED",
            "stage_data": {"plans_count": 3, "default_currency": "TRY"},
        },
    )
    assert adv_resp.status_code == 200
    adv_data = adv_resp.json()
    assert adv_data["current_stage"] == "PLANS_DEFINED"
    assert "PLANS_DEFINED" in adv_data["step_data"]

    # 4. Complete onboarding
    comp_resp = await api_client.post(
        "/api/v1/onboarding/advance",
        headers=headers,
        json={
            "next_stage": "COMPLETED",
            "stage_data": {"checklist_verified": True},
        },
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["current_stage"] == "COMPLETED"
    assert comp_data["is_completed"] is True
    assert comp_data["completed_at"] is not None
