"""Login rate limit: shared across processes, keyed per identifier, fail-open.

The limiter guards the one unauthenticated write in the API, so its failure
modes matter more than its happy path: it must not leak the budget across
identifiers, must not go down when Redis does, and must not retain PII.
"""

import asyncio
import hashlib

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.api.middleware.rate_limit import SimpleRateLimitMiddleware

LOGIN_PATH = "/api/v1/auth/login"


def _build_app(**kwargs):
    """Wrap the route in the middleware directly, so the test holds its instance.

    `add_middleware` would bury it in a stack Starlette only builds on startup.
    """

    async def login(request: Request):
        await request.json()
        return JSONResponse({"ok": True})

    inner = Starlette(routes=[Route(LOGIN_PATH, login, methods=["POST"])])
    return SimpleRateLimitMiddleware(inner, max_requests=3, window_seconds=60, **kwargs)


def _client(app):
    from httpx import ASGITransport, AsyncClient

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _post(client, email: str):
    return await client.post(LOGIN_PATH, json={"email": email, "password": "x"})


@pytest.mark.asyncio
async def test_limit_is_per_identifier_and_returns_429():
    app = _build_app()
    async with _client(app) as client:
        # Force the in-process path: no Redis in this unit test.
        app._redis_failed = True

        for _ in range(3):
            assert (await _post(client, "a@example.com")).status_code == 200

        blocked = await _post(client, "a@example.com")
        assert blocked.status_code == 429
        assert blocked.headers["Retry-After"] == "60"
        # User-facing copy is Turkish and actionable, never a stack detail.
        assert "tekrar deneyin" in blocked.json()["detail"]

        # A different identifier still has its own budget.
        assert (await _post(client, "b@example.com")).status_code == 200


@pytest.mark.asyncio
async def test_identifier_is_hashed_not_stored_raw():
    app = _build_app()
    async with _client(app) as client:
        app._redis_failed = True
        await _post(client, "secret.user@example.com")

    keys = list(app._hits.keys())
    assert keys, "the request should have been counted"
    assert all("secret.user@example.com" not in k for k in keys)
    digest = hashlib.sha256(b"secret.user@example.com").hexdigest()[:32]
    assert any(digest in k for k in keys)


@pytest.mark.asyncio
async def test_redis_failure_falls_open_to_in_process_window():
    """A cache outage must degrade the limiter, never take login down."""
    app = _build_app()
    mw = app

    class ExplodingRedis:
        def pipeline(self):
            raise ConnectionError("redis down")

    mw._redis = ExplodingRedis()

    async with _client(app) as client:
        assert (await _post(client, "c@example.com")).status_code == 200
        assert mw._redis_failed is True  # marked degraded, not retried per request
        for _ in range(2):
            assert (await _post(client, "c@example.com")).status_code == 200
        # Still enforcing, just locally.
        assert (await _post(client, "c@example.com")).status_code == 429


@pytest.mark.asyncio
async def test_device_auth_is_limited_per_device_id():
    device_path = "/api/v1/devices/auth"

    async def auth(request: Request):
        await request.json()
        return JSONResponse({"ok": True})

    inner = Starlette(routes=[Route(device_path, auth, methods=["POST"])])
    app = SimpleRateLimitMiddleware(inner, max_requests=3, window_seconds=60)
    app._redis_failed = True
    async with _client(app) as client:
        payload = {
            "device_id": "11111111-1111-1111-1111-111111111111",
            "tenant_id": "22222222-2222-2222-2222-222222222222",
            "api_key": "x",
        }
        for _ in range(3):
            assert (
                await client.post(device_path, json=payload)
            ).status_code == 200
        blocked = await client.post(device_path, json=payload)
        assert blocked.status_code == 429
        other = dict(payload)
        other["device_id"] = "33333333-3333-3333-3333-333333333333"
        assert (await client.post(device_path, json=other)).status_code == 200


@pytest.mark.asyncio
async def test_body_is_readable_by_the_endpoint_after_inspection():
    """The middleware consumes the body to key on it; the handler must still get it."""
    app = _build_app()
    async with _client(app) as client:
        app._redis_failed = True
        res = await _post(client, "d@example.com")
        assert res.status_code == 200
        assert res.json() == {"ok": True}


@pytest.mark.asyncio
async def test_redis_window_is_shared_across_middleware_instances():
    """Two API processes must share one budget — the reason this moved to Redis."""
    redis = pytest.importorskip("redis.asyncio", reason="redis client not installed")
    from app.core.config import settings

    client_a = redis.Redis.from_url(str(settings.REDIS_URL))
    try:
        await client_a.ping()
    except Exception:
        await client_a.aclose()
        pytest.skip("no Redis reachable in this environment")

    email = f"shared-{asyncio.get_running_loop().time()}@example.com"
    digest = hashlib.sha256(email.encode()).hexdigest()[:32]
    await client_a.delete(f"rl:{LOGIN_PATH}:{digest}")

    app_one, app_two = _build_app(), _build_app()
    try:
        async with _client(app_one) as c1, _client(app_two) as c2:
            assert (await _post(c1, email)).status_code == 200
            assert (await _post(c2, email)).status_code == 200
            assert (await _post(c1, email)).status_code == 200
            # Fourth request against a max of 3 — regardless of which process.
            assert (await _post(c2, email)).status_code == 429
    finally:
        await client_a.delete(f"rl:{LOGIN_PATH}:{digest}")
        await client_a.aclose()
