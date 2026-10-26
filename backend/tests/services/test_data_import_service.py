"""Service-level CSV import validation and commit branches."""

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.data_import import DataImportRow, ImportBatchStatus, ImportRowStatus
from app.models.member import Member
from app.models.membership import Membership, Plan, PlanVersion
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.models.user import User
from app.services.data_import import DataImportService


@pytest_asyncio.fixture
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    maker = async_sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        yield session


async def _tenant_user(db: AsyncSession) -> tuple[Tenant, User]:
    org = Organization(name="Imp Org", domain=f"imp-{uuid4().hex[:8]}.com")
    db.add(org)
    await db.flush()
    tenant = Tenant(
        id=uuid4(),
        name="Imp T",
        organization_id=org.id,
        location_code=f"IM-{uuid4().hex[:6]}",
    )
    db.add(tenant)
    await db.flush()
    user = User(
        email=f"imp-{uuid4().hex[:8]}@example.com",
        hashed_password="x",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return tenant, user


@pytest.mark.asyncio
async def test_preview_rejects_empty_oversize_and_missing_headers(db_session):
    tenant, user = await _tenant_user(db_session)
    with pytest.raises(ValueError, match="boş"):
        await DataImportService.create_preview_batch(
            db_session, tenant.id, user.id, "empty.csv", ""
        )
    with pytest.raises(ValueError, match="2 MB"):
        await DataImportService.create_preview_batch(
            db_session,
            tenant.id,
            user.id,
            "huge.csv",
            "x" * (2 * 1024 * 1024 + 1),
        )
    with pytest.raises(ValueError, match="first_name"):
        await DataImportService.create_preview_batch(
            db_session,
            tenant.id,
            user.id,
            "bad.csv",
            "email,phone\na@b.c,555\n",
        )


@pytest.mark.asyncio
async def test_preview_maps_turkish_headers_and_validates_rows(db_session):
    tenant, user = await _tenant_user(db_session)
    csv_text = (
        "ad,soyad,eposta,telefon,uye_no\n"
        "\n"
        "Ali,Veli,ali@test.com,+905551112233,MBR-1\n"
        ",Yok,bad-email,+cmd|calc,=HYPERLINK\n"
        "Ayse,Kaya,ayse@test.com,-notaphone,MBR-2\n"
        "Can,Demir,can@test.com,5550001122,\n"
    )
    batch = await DataImportService.create_preview_batch(
        db_session, tenant.id, user.id, "tr.csv", csv_text
    )
    assert batch.total_rows == 4
    assert batch.valid_rows == 2
    assert batch.invalid_rows == 2
    assert batch.status == ImportBatchStatus.PREVIEW

    stored = list(
        (
            await db_session.execute(
                select(DataImportRow)
                .where(DataImportRow.batch_id == batch.id)
                .order_by(DataImportRow.row_number)
            )
        )
        .scalars()
        .all()
    )
    assert stored[0].status == ImportRowStatus.VALID
    assert stored[0].parsed_data["first_name"] == "Ali"
    assert stored[0].parsed_data["phone"] == "+905551112233"
    assert stored[1].status == ImportRowStatus.INVALID
    assert "İsim" in (stored[1].error_message or "")
    assert "e-posta" in (stored[1].error_message or "")
    assert "formül" in (stored[1].error_message or "")
    assert stored[2].status == ImportRowStatus.INVALID
    assert "phone" in (stored[2].error_message or "")
    assert stored[3].status == ImportRowStatus.VALID
    assert stored[3].parsed_data["member_number"] is None


@pytest.mark.asyncio
async def test_commit_creates_members_dedupes_and_attaches_plan(db_session):
    tenant, user = await _tenant_user(db_session)
    plan = Plan(tenant_id=tenant.id, name="Imported")
    db_session.add(plan)
    await db_session.flush()
    published = PlanVersion(
        tenant_id=tenant.id,
        plan_id=plan.id,
        version=1,
        price_amount_minor=19900,
        currency="TRY",
        billing_cycle_months=1,
        is_published=True,
    )
    unpublished = PlanVersion(
        tenant_id=tenant.id,
        plan_id=plan.id,
        version=2,
        price_amount_minor=29900,
        currency="TRY",
        billing_cycle_months=1,
        is_published=False,
    )
    db_session.add_all([published, unpublished])
    existing = Member(
        tenant_id=tenant.id,
        member_number="DUP-1",
        first_name="Old",
        last_name="Row",
        status="ACTIVE",
    )
    db_session.add(existing)
    await db_session.commit()

    csv_text = (
        "first_name,last_name,email,member_number,plan_id,start_date\n"
        f"New,One,new1@test.com,DUP-1,{plan.id},2026-01-15T00:00:00\n"
        f"New,Two,new2@test.com,FRESH-1,{plan.id},2026-02-01T00:00:00+00:00\n"
        "New,Three,new3@test.com,FRESH-2,not-a-uuid,bad-date\n"
        f"New,Four,new4@test.com,,{uuid4()},2026-03-01\n"
    )
    batch = await DataImportService.create_preview_batch(
        db_session, tenant.id, user.id, "commit.csv", csv_text
    )
    assert batch.valid_rows == 4

    committed = await DataImportService.commit_batch(db_session, tenant.id, batch.id)
    assert committed.status == ImportBatchStatus.COMPLETED
    assert committed.imported_rows == 4
    assert committed.completed_at is not None

    members = list(
        (await db_session.execute(select(Member).where(Member.tenant_id == tenant.id)))
        .scalars()
        .all()
    )
    assert len(members) == 5  # 1 pre-existing + 4 imported
    imported = [m for m in members if m.first_name == "New"]
    numbers = {m.member_number for m in imported}
    assert any(n.startswith("DUP-1-") for n in numbers)
    assert "FRESH-1" in numbers
    assert "FRESH-2" in numbers
    assert any(n.startswith("IMP-") for n in numbers)

    memberships = list(
        (
            await db_session.execute(
                select(Membership).where(Membership.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(memberships) == 2
    assert {m.plan_version_id for m in memberships} == {published.id}


@pytest.mark.asyncio
async def test_commit_rejects_missing_wrong_tenant_and_already_processed(db_session):
    tenant, user = await _tenant_user(db_session)
    other_org = Organization(name="Other Imp", domain=f"oi-{uuid4().hex[:8]}.com")
    db_session.add(other_org)
    await db_session.flush()
    other = Tenant(
        id=uuid4(),
        name="Other Imp T",
        organization_id=other_org.id,
        location_code=f"OI-{uuid4().hex[:6]}",
    )
    db_session.add(other)
    await db_session.commit()

    with pytest.raises(ValueError, match="bulunamadı"):
        await DataImportService.commit_batch(db_session, tenant.id, uuid4())

    batch = await DataImportService.create_preview_batch(
        db_session,
        tenant.id,
        user.id,
        "once.csv",
        "first_name,last_name\nAda,Lovelace\n",
    )
    with pytest.raises(ValueError, match="bulunamadı"):
        await DataImportService.commit_batch(db_session, other.id, batch.id)

    await DataImportService.commit_batch(db_session, tenant.id, batch.id)
    with pytest.raises(ValueError, match="işlendi"):
        await DataImportService.commit_batch(db_session, tenant.id, batch.id)
