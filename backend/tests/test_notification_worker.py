"""Notification worker cycle is callable and commits without looping forever."""

from unittest.mock import patch

import pytest

from app.workers.notification import run_cycle


@pytest.mark.asyncio
async def test_notification_run_cycle_on_empty_queue(pg_session_maker):
    # Use the test sessionmaker; the module-level engine is bound to another loop.
    with patch("app.workers.notification.AsyncSessionLocal", pg_session_maker):
        processed = await run_cycle()
    assert processed == 0
