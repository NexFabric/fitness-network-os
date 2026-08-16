#!/usr/bin/env python3
"""Prove SQLAlchemy+asyncpg can open a TLS Postgres session.

Spins a throwaway postgres:16 with ssl=on and a generated cert, then
connects with database_ssl_connect_arg (ssl=True for sslmode=require).
This is transport proof, not production RPO.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

CONTAINER = os.environ.get("TLS_PROOF_CONTAINER", "fitness-os-tls-proof")
IMAGE = os.environ.get("TLS_PROOF_IMAGE", "postgres:16")
PASSWORD = "tls-proof-pass"


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kwargs)


def _cleanup() -> None:
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER],
        check=False,
        capture_output=True,
        text=True,
    )


def _wait_ready() -> None:
    for _ in range(40):
        probe = subprocess.run(
            [
                "docker",
                "exec",
                CONTAINER,
                "pg_isready",
                "-U",
                "postgres",
            ],
            check=False,
            capture_output=True,
        )
        if probe.returncode == 0:
            return
        time.sleep(0.5)
    raise RuntimeError("tls postgres did not become ready")


async def _select_one(url: str) -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.config import database_ssl_connect_arg

    ssl = database_ssl_connect_arg(url)
    if ssl is None:
        raise RuntimeError("expected ssl connect arg for sslmode=require")
    engine = create_async_engine(url, connect_args={"ssl": ssl})
    async with engine.connect() as conn:
        value = (await conn.execute(text("SELECT 1"))).scalar_one()
    await engine.dispose()
    if value != 1:
        raise RuntimeError(f"unexpected SELECT 1 result: {value}")


def main() -> int:
    if shutil.which("docker") is None:
        print("TLS proof: SKIP (docker not available)")
        return 2
    if shutil.which("openssl") is None:
        print("TLS proof: SKIP (openssl not available)")
        return 2

    work = Path(tempfile.mkdtemp(prefix="fitness-os-tls-"))
    try:
        _cleanup()
        cert = work / "server.crt"
        key = work / "server.key"
        _run(
            [
                "openssl",
                "req",
                "-new",
                "-x509",
                "-days",
                "1",
                "-nodes",
                "-subj",
                "/CN=localhost",
                "-out",
                str(cert),
                "-keyout",
                str(key),
            ]
        )
        key.chmod(0o600)
        _run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                CONTAINER,
                "-e",
                f"POSTGRES_PASSWORD={PASSWORD}",
                "-v",
                f"{cert}:/var/lib/postgresql/server.crt:ro",
                "-v",
                f"{key}:/var/lib/postgresql/server.key:ro",
                "-p",
                "55432:5432",
                IMAGE,
                "-c",
                "ssl=on",
                "-c",
                "ssl_cert_file=/var/lib/postgresql/server.crt",
                "-c",
                "ssl_key_file=/var/lib/postgresql/server.key",
            ]
        )
        # postgres image may refuse the key because it is root-owned; fix inside.
        _run(
            [
                "docker",
                "exec",
                "-u",
                "root",
                CONTAINER,
                "bash",
                "-lc",
                (
                    "chown postgres:postgres /var/lib/postgresql/server.key "
                    "/var/lib/postgresql/server.crt && "
                    "chmod 600 /var/lib/postgresql/server.key"
                ),
            ]
        )
        subprocess.run(
            ["docker", "restart", CONTAINER], check=True, capture_output=True
        )
        _wait_ready()
        url = (
            f"postgresql+asyncpg://postgres:{PASSWORD}@127.0.0.1:55432"
            "/postgres?sslmode=require"
        )
        asyncio.run(_select_one(url))
        print("TLS proof: PASS SQLAlchemy+asyncpg sslmode=require")
        return 0
    finally:
        _cleanup()
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
