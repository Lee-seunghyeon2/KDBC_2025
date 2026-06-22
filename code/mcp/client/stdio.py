"""MCP Server를 하위 프로세스로 실행하는 stdio 연결 모듈입니다."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class StdioServerParameters:
    """MCP Server 프로세스 실행 정보를 담습니다."""
    command: str
    args: list[str] | None = None
    env: dict[str, str] | None = None
    cwd: str | None = None


@asynccontextmanager
async def stdio_client(params: StdioServerParameters) -> AsyncIterator[tuple[asyncio.StreamReader, asyncio.StreamWriter]]:
    """Server를 실행하고 stdin/stdout 스트림을 제공하는 비동기 context manager입니다."""
    environment = os.environ.copy()
    environment.update(params.env or {})
    process = await asyncio.create_subprocess_exec(
        params.command,
        *(params.args or []),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=environment,
        cwd=params.cwd,
    )
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("MCP Server의 stdio 연결을 만들지 못했습니다.")

    try:
        yield process.stdout, process.stdin
    finally:
        if process.stdin:
            process.stdin.close()
            try:
                await process.stdin.wait_closed()
            except Exception:
                pass
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
