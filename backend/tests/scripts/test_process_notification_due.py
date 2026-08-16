"""Unit tests for ops CLI process_notification_due (mocked service / session)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from scripts.process_notification_due import (
    build_parser,
    main,
    process_due_for_tenant,
)


def test_build_parser_tenant_id():
    tenant = uuid4()
    args = build_parser().parse_args(
        [str(tenant), "--limit", "10", "--max-attempts", "3"]
    )
    assert args.tenant_id == tenant
    assert args.limit == 10
    assert args.max_attempts == 3


@pytest.mark.asyncio
async def test_process_due_for_tenant_sets_rls_and_returns_stats():
    tenant_id = uuid4()
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    # NotificationService is imported inside process_due_for_tenant (lazy).
    with patch("app.services.notification.NotificationService") as svc_cls:
        instance = MagicMock()
        instance.process_due_failed = AsyncMock(
            return_value={"sent": 2, "failed": 1, "dead": 0}
        )
        svc_cls.return_value = instance

        stats = await process_due_for_tenant(
            session, tenant_id, limit=25, max_attempts=4
        )

    assert stats == {"sent": 2, "failed": 1, "dead": 0}
    instance.process_due_failed.assert_awaited_once_with(
        tenant_id, limit=25, max_attempts=4
    )
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
    # RLS SET LOCAL issued (tenant id is bound, not interpolated)
    assert session.execute.await_count >= 1
    first = session.execute.await_args_list[0]
    sql = str(first.args[0])
    assert "app.current_tenant_id" in sql
    params = first.args[1] if len(first.args) > 1 else first.kwargs.get("parameters") or first.kwargs
    if isinstance(params, dict):
        assert params.get("tid") == str(tenant_id)
    else:
        assert str(tenant_id) in str(first)


@pytest.mark.asyncio
async def test_process_due_for_tenant_rolls_back_on_error():
    tenant_id = uuid4()
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    with patch("app.services.notification.NotificationService") as svc_cls:
        instance = MagicMock()
        instance.process_due_failed = AsyncMock(side_effect=RuntimeError("boom"))
        svc_cls.return_value = instance

        with pytest.raises(RuntimeError, match="boom"):
            await process_due_for_tenant(session, tenant_id)

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_main_prints_json_and_exits_0(capsys):
    tenant_id = uuid4()
    fake_result = {
        "tenant_id": str(tenant_id),
        "sent": 0,
        "failed": 0,
        "dead": 0,
    }

    async def _fake(*_a, **_k):
        return fake_result

    with patch(
        "scripts.process_notification_due._async_main",
        side_effect=_fake,
    ):
        code = main([str(tenant_id)])
    assert code == 0
    out = capsys.readouterr().out.strip()
    assert json.loads(out) == fake_result


def test_main_rejects_bad_limit():
    code = main([str(uuid4()), "--limit", "0"])
    assert code == 2
