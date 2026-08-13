"""Plan catalogue + membership creation over HTTP.

This closes API-1: before it, a membership could only exist where a seed script
had written one, so the whole lifecycle surface had nothing to act on.

The interesting assertions are the refusals — an unpublished plan version must
not be sellable, a member must not end up with two live memberships, and the
version number must come from the server.
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.session import get_db
from app.main import app
from tests.api.test_auth_login import _seed_user


@pytest.fixture
async def api_client(pg_session_maker):
    async def override_get_db():
        async with pg_session_maker() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def _seed_owner(api_client, pg_session_maker):
    """A user holding memberships:read/write, plus a member to sell to."""
    email = f"plans-{uuid4().hex[:8]}@example.com"
    password = "AdminPassword1!"
    async with pg_session_maker() as db:
        user, tenant = await _seed_user(db, email=email, password=password)

        from app.models.rbac import Permission, Role, UserRole

        # A private role carrying exactly what these tests need. `_seed_user`
        # hands out the shared GYM_OWNER row, which other tests in the suite
        # also mutate — depending on it makes this file pass or fail by
        # execution order rather than by behaviour.
        perms = []
        # members:read grants the endpoint; members:read:all grants the rows.
        # Without the latter the caller is treated as a trainer-scoped reader and
        # only sees assigned members (Phase 27 row scoping) — correct, and worth
        # spelling out here so the 403 is never mistaken for a permission bug.
        for needed in (
            "memberships:read",
            "memberships:write",
            "members:read",
            "members:read:all",
        ):
            perm = (
                await db.execute(select(Permission).where(Permission.name == needed))
            ).scalar_one_or_none()
            if perm is None:
                perm = Permission(name=needed, description=needed)
                db.add(perm)
                await db.flush()
            perms.append(perm)

        # Permissions are passed at construction: touching `role.permissions` on
        # a pending object would lazy-load under async and raise MissingGreenlet.
        role = Role(
            name=f"plans-role-{uuid4().hex[:8]}",
            description="plan catalogue tests",
            permissions=perms,
        )
        db.add(role)
        await db.flush()

        role_row = (
            await db.execute(select(UserRole).where(UserRole.user_id == user.id))
        ).scalar_one()
        role_row.role_id = role.id
        await db.commit()

    login = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200
    cookie = login.cookies["session_token"]
    headers = {"X-Tenant-ID": str(tenant.id)}

    async with pg_session_maker() as db:
        from sqlalchemy import text

        from app.models.member import Member

        await db.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": str(tenant.id)},
        )
        member = Member(
            tenant_id=tenant.id,
            member_number=f"M-{uuid4().hex[:8]}",
            first_name="Test",
            last_name="Üye",
            status="ACTIVE",
        )
        db.add(member)
        await db.commit()
        member_id = str(member.id)

    return {"cookie": cookie, "headers": headers, "member_id": member_id}


@pytest.mark.asyncio
async def test_plan_catalogue_and_membership_start(api_client, pg_session_maker):
    ctx = await _seed_owner(api_client, pg_session_maker)
    cookies = {"session_token": ctx["cookie"]}
    headers = ctx["headers"]

    plan_res = await api_client.post(
        "/api/v1/plans",
        headers=headers,
        cookies=cookies,
        json={"name": "Aylık Sınırsız", "description": "Tüm şubeler"},
    )
    assert plan_res.status_code == 201
    plan_id = plan_res.json()["id"]

    version_res = await api_client.post(
        f"/api/v1/plans/{plan_id}/versions",
        headers=headers,
        cookies=cookies,
        json={"price_amount_minor": 49900, "billing_cycle_months": 1},
    )
    assert version_res.status_code == 201
    version = version_res.json()
    # Version numbering is the server's, and money stays in minor units.
    assert version["version"] == 1
    assert version["price_amount_minor"] == 49900
    assert version["currency"] == "TRY"
    assert version["is_published"] is False
    version_id = version["id"]

    # An unpublished version is a draft, not a sellable product.
    early = await api_client.post(
        "/api/v1/memberships",
        headers=headers,
        cookies=cookies,
        json={"member_id": ctx["member_id"], "plan_version_id": version_id},
    )
    assert early.status_code == 400
    assert "PlanVersion" in early.json()["detail"]

    published = await api_client.post(
        f"/api/v1/plans/versions/{version_id}/publish", headers=headers, cookies=cookies
    )
    assert published.status_code == 200
    assert published.json()["is_published"] is True

    # Publishing is one-way.
    again = await api_client.post(
        f"/api/v1/plans/versions/{version_id}/publish", headers=headers, cookies=cookies
    )
    assert again.status_code == 400

    started = await api_client.post(
        "/api/v1/memberships",
        headers=headers,
        cookies=cookies,
        json={"member_id": ctx["member_id"], "plan_version_id": version_id},
    )
    assert started.status_code == 201
    membership = started.json()
    assert membership["status"] == "ACTIVE"
    # The price is snapshotted, so a later plan version cannot rewrite history.
    assert membership["price_snapshot"] == 49900
    assert membership["price_snapshot_currency"] == "TRY"

    # A second live membership for the same member is refused.
    duplicate = await api_client.post(
        "/api/v1/memberships",
        headers=headers,
        cookies=cookies,
        json={"member_id": ctx["member_id"], "plan_version_id": version_id},
    )
    assert duplicate.status_code == 400

    # And the lifecycle surface now has something to act on.
    listed = await api_client.get(
        f"/api/v1/members/{ctx['member_id']}/memberships", headers=headers, cookies=cookies
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    frozen = await api_client.post(
        f"/api/v1/memberships/{membership['id']}/freeze",
        headers=headers,
        cookies=cookies,
        json={"start_date": membership["start_date"][:10], "reason": "tatil"},
    )
    assert frozen.status_code == 200


@pytest.mark.asyncio
async def test_second_version_increments_and_price_is_validated(
    api_client, pg_session_maker
):
    ctx = await _seed_owner(api_client, pg_session_maker)
    cookies = {"session_token": ctx["cookie"]}
    headers = ctx["headers"]

    plan_id = (
        await api_client.post(
            "/api/v1/plans", headers=headers, cookies=cookies, json={"name": "Yıllık"}
        )
    ).json()["id"]

    for expected in (1, 2, 3):
        res = await api_client.post(
            f"/api/v1/plans/{plan_id}/versions",
            headers=headers,
            cookies=cookies,
            json={"price_amount_minor": 1000 * expected, "billing_cycle_months": 12},
        )
        assert res.status_code == 201
        assert res.json()["version"] == expected

    negative = await api_client.post(
        f"/api/v1/plans/{plan_id}/versions",
        headers=headers,
        cookies=cookies,
        json={"price_amount_minor": -1, "billing_cycle_months": 1},
    )
    assert negative.status_code == 422

    zero_cycle = await api_client.post(
        f"/api/v1/plans/{plan_id}/versions",
        headers=headers,
        cookies=cookies,
        json={"price_amount_minor": 100, "billing_cycle_months": 0},
    )
    assert zero_cycle.status_code == 422

    missing_plan = await api_client.post(
        f"/api/v1/plans/{uuid4()}/versions",
        headers=headers,
        cookies=cookies,
        json={"price_amount_minor": 100, "billing_cycle_months": 1},
    )
    assert missing_plan.status_code == 404


@pytest.mark.asyncio
async def test_plan_catalogue_requires_membership_permissions(
    api_client, pg_session_maker
):
    """A user without memberships:write cannot mint sellable products."""
    email = f"noperm-{uuid4().hex[:8]}@example.com"
    password = "AdminPassword1!"
    async with pg_session_maker() as db:
        user, tenant = await _seed_user(db, email=email, password=password)

        from app.models.rbac import Role, UserRole

        # Point this user at a private, permission-less role instead of stripping
        # the shared GYM_OWNER row: `_seed_user` reuses that role, so clearing it
        # would silently disarm authorization for every other test in the run.
        bare = Role(name=f"noperm-role-{uuid4().hex[:8]}", description="no permissions")
        db.add(bare)
        await db.flush()
        role_row = (
            await db.execute(select(UserRole).where(UserRole.user_id == user.id))
        ).scalar_one()
        role_row.role_id = bare.id
        await db.commit()

    login = await api_client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    cookie = login.cookies["session_token"]

    res = await api_client.post(
        "/api/v1/plans",
        headers={"X-Tenant-ID": str(tenant.id)},
        cookies={"session_token": cookie},
        json={"name": "Yetkisiz"},
    )
    assert res.status_code == 403
