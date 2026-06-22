"""원본 프로젝트의 FastMCP decorator 인터페이스를 유지한 경량 Server 구현입니다."""

from __future__ import annotations

import asyncio
import inspect
import json
import sys
from typing import Any, Callable


class FastMCP:
    """Tool decorator, 등록 목록 조회, stdio JSON 요청 처리를 제공하는 간단한 MCP Server입니다."""

    def __init__(self, name: str):
        self.name = name
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self, name: str):
        """함수를 MCP Tool로 등록합니다."""
        def wrapper(function: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[name] = function
            return function
        return wrapper

    def list_tools(self) -> list[dict[str, Any]]:
        result = []
        for name, function in self.tools.items():
            signature = inspect.signature(function)
            properties: dict[str, Any] = {}
            for parameter_name, parameter in signature.parameters.items():
                schema: dict[str, Any] = {"type": "integer" if parameter.annotation is int else "string"}
                if parameter.default is not inspect.Parameter.empty:
                    schema["default"] = parameter.default
                properties[parameter_name] = schema
            result.append(
                {
                    "name": name,
                    "description": inspect.getdoc(function) or "설명이 제공되지 않았습니다.",
                    "inputSchema": {"type": "object", "properties": properties},
                }
            )
        return result

    def _call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self.tools:
            return {"content": [{"type": "text", "text": f"알 수 없는 Tool입니다: {name}"}], "isError": True}
        try:
            output = self.tools[name](**arguments)
            if inspect.isawaitable(output):
                output = asyncio.run(output)
            text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            return {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as exc:
            return {"content": [{"type": "text", "text": f"Tool 실행 중 오류: {exc}"}], "isError": True}

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {}) or {}
        if method == "initialize":
            result = {"serverInfo": {"name": self.name, "version": "1.0.0"}, "capabilities": {"tools": {}}}
        elif method == "tools/list":
            result = {"tools": self.list_tools()}
        elif method == "tools/call":
            result = self._call(params.get("name", ""), params.get("arguments", {}) or {})
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"지원하지 않는 메서드입니다: {method}"}}
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def run(self) -> None:
        """한 줄 JSON 요청을 받아 한 줄 JSON 응답으로 반환합니다."""
        print(f"[MCP Server] {self.name} 시작. 등록 Tool: {list(self.tools)}", file=sys.stderr)
        for raw_line in sys.stdin:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                request = json.loads(raw_line)
                response = self.handle_request(request)
            except json.JSONDecodeError:
                response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "JSON 형식이 올바르지 않습니다."}}
            print(json.dumps(response, ensure_ascii=False), flush=True)
