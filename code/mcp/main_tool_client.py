"""MCP Tool을 직접 호출하는 Client 실행 파일입니다.

원본 `main2.py`의 Tool 선택·호출·결과 요약 흐름을 CLI 형태로 정리했습니다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from . import ClientSession
from .client.stdio import StdioServerParameters, stdio_client


def format_video_summary(tool_name: str, result: dict[str, Any]) -> str:
    """원본 main.py의 Tool 결과 요약 형식을 정리합니다."""
    if result.get("status") != "ok":
        return f"[오류] {tool_name}: {result.get('message', '알 수 없는 오류')}"
    videos = result.get("videos", [])
    if not videos:
        return f"[결과 없음] {tool_name}"
    lines = []
    for index, video in enumerate(videos, 1):
        lines.append(
            f"{index}. 제목: {video.get('title', '제목 없음')}\n"
            f"   채널: {video.get('channel', '채널 정보 없음')}\n"
            f"   링크: {video.get('video_url', '링크 없음')}"
        )
    return f"🔥 {tool_name} 결과\n" + "\n".join(lines)


async def call_tool(tool_name: str, arguments: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Server를 실행하고 Tool 목록과 호출 결과를 반환합니다."""
    server_file = Path(__file__).resolve().parent / "mcp_server.py"
    code_root = server_file.parent.parent
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp.mcp_server"],
        cwd=str(code_root),
    )
    async with stdio_client(parameters) as (read, write):
        session = ClientSession(read, write)
        await session.initialize()
        tools = await session.list_tools()
        response = await session.call_tool(tool_name, arguments)
        text = response.content[0] if response.content else "{}"
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            result = {"status": "error", "message": text, "videos": []}
        return tools, result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KDBC 2025 MCP Tool Client")
    parser.add_argument("--tool", default="youtube_trend", choices=["youtube_trend", "youtube_music", "youtube_artist_search", "calculator"])
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--artists", type=str, default="", help="쉼표 또는 공백으로 구분한 관심 가수 목록")
    parser.add_argument("--operation", type=str, default="+")
    parser.add_argument("--numbers", type=float, nargs="*", default=[1, 2])
    parser.add_argument("--json", action="store_true", help="요약 대신 원본 JSON을 출력합니다.")
    return parser.parse_args()


async def main_async() -> None:
    args = parse_args()
    if args.tool == "youtube_artist_search":
        artists = [item.strip() for item in args.artists.replace(",", " ").split() if item.strip()]
        if not artists:
            raise ValueError("youtube_artist_search에는 --artists 입력이 필요합니다.")
        arguments = {"artists": artists, "max_results": args.max_results}
    elif args.tool == "calculator":
        arguments = {"operation": args.operation, "numbers": args.numbers}
    else:
        arguments = {"max_results": args.max_results}

    tools, result = await call_tool(args.tool, arguments)
    print("등록된 Tool:", ", ".join(tool["name"] for tool in tools))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_video_summary(args.tool, result))


if __name__ == "__main__":
    asyncio.run(main_async())
