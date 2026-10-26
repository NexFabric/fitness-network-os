"""Real TLS connection smoke.

The weekly ops-drills workflow always runs scripts/tls_connection_proof.py.
This test is opt-in so the required pytest job does not start a second
Postgres. Set FITNESS_OS_TLS_SMOKE=1 to execute it locally.
"""

import os
import shutil

import pytest

from scripts.tls_connection_proof import main


@pytest.mark.skipif(
    os.environ.get("FITNESS_OS_TLS_SMOKE") != "1",
    reason="set FITNESS_OS_TLS_SMOKE=1 to run the Docker TLS proof",
)
def test_asyncpg_tls_connection_smoke():
    if shutil.which("docker") is None or shutil.which("openssl") is None:
        pytest.skip("docker+openssl required")
    code = main()
    if code == 2:
        pytest.skip("tls proof environment unavailable")
    assert code == 0
