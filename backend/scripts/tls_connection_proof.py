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
import sys
import tempfile
import time
from pathlib import Path

# uv run python scripts/*.py puts scripts/ on sys.path[0], not backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CONTAINER = os.environ.get("TLS_PROOF_CONTAINER", "fitness-os-tls-proof")
IMAGE = os.environ.get("TLS_PROOF_IMAGE", "postgres:16")
PASSWORD = "tls-proof-pass"
# Official postgres:16 (Debian) image: postgres uid/gid is 999.
POSTGRES_UID = 999
POSTGRES_GID = 999


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(cmd, check=True, text=True, capture_output=True, **kwargs)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        if detail:
            raise RuntimeError(f"{cmd[0]} failed ({exc.returncode}): {detail}") from exc
        raise


def _cleanup() -> None:
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER],
        check=False,
        capture_output=True,
        text=True,
    )


def _chown(path: Path, uid: int, gid: int) -> None:
    try:
        os.chown(path, uid, gid)
        return
    except OSError:
        if os.geteuid() == 0:
            raise
    _run(["sudo", "-n", "chown", f"{uid}:{gid}", str(path)])


def _own_for_postgres(*paths: Path) -> None:
    """Own certs as 999:999 on the host before bind-mount.

    postgres:16 refuses ssl=on when the key is runner-owned; the process
    then exits and a later docker exec chown races a dead PID.
    """
    for path in paths:
        _chown(path, POSTGRES_UID, POSTGRES_GID)


def _rmtree(path: Path) -> None:
    try:
        shutil.rmtree(path)
        return
    except OSError:
        pass
    subprocess.run(
        ["sudo", "-n", "rm", "-rf", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    shutil.rmtree(path, ignore_errors=True)


def _container_logs() -> str:
    logs = subprocess.run(
        ["docker", "logs", CONTAINER],
        check=False,
        capture_output=True,
        text=True,
    )
    return (logs.stderr or logs.stdout or "").strip()


def _wait_ready() -> None:
    for _ in range(40):
        state = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
            check=False,
            capture_output=True,
            text=True,
        )
        if state.returncode == 0 and state.stdout.strip() == "false":
            break
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
    detail = _container_logs()
    raise RuntimeError(f"tls postgres did not become ready: {detail}")


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
        cert.chmod(0o644)
        key.chmod(0o600)
        _own_for_postgres(cert, key)
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
        _rmtree(work)


if __name__ == "__main__":
    raise SystemExit(main())
