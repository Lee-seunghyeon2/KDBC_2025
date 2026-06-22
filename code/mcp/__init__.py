"""프로젝트용 경량 MCP 인터페이스입니다.

원본 프로젝트의 Server/Client 구조를 유지하되, 공개 버전에서는
stdio 기반 JSON 요청·응답이 실제로 동작하도록 정리했습니다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResponse:
    """Tool 호출 결과를 표현하는 간단한 응답 객체입니다."""
    content: list[str]
    is_error: bool = False


class ClientSession:
    """stdio 스트림을 통해 JSON-RPC 스타일 요청을 보내는 MCP Client Session입니다."""

    def __init__(self, read: Any, write: Any):
        self.read = read
        self.write = write
        self.request_id = 0

    async def _request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {},
        }
        self.write.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
        await self.write.drain()
        line = await self.read.readline()
        if not line:
            raise RuntimeError("MCP Server가 응답 없이 종료되었습니다.")
        response = json.loads(line.decode("utf-8"))
        if "error" in response:
            raise RuntimeError(response["error"].get("message", "MCP 요청 처리 중 오류가 발생했습니다."))
        return response.get("result", {})

    async def initialize(self) -> dict[str, Any]:
        return await self._request("initialize", {"clientInfo": {"name": "kdbc-project-client"}})

    async def list_tools(self) -> list[dict[str, Any]]:
        return (await self._request("tools/list")).get("tools", [])

    async def call_tool(self, method: str, arguments: dict[str, Any] | None = None) -> ToolResponse:
        result = await self._request("tools/call", {"name": method, "arguments": arguments or {}})
        content = result.get("content", [])
        text_items = [item.get("text", "") if isinstance(item, dict) else str(item) for item in content]
        return ToolResponse(content=text_items, is_error=bool(result.get("isError", False)))
