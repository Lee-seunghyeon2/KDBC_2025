from mcp.server.fastmcp import FastMCP
from tools.youtube_trend_tool import get_trending_videos  # 🔹 Tool 함수 import
from tools.youtube_music_tool import get_trending_music_videos
import asyncio
import json

mcp = FastMCP("YouTube Trend Tool")

# 🔹 MCP에 등록할 Tool
@mcp.tool(name="youtube_trend")
def youtube_trend(max_results: int = 3) -> str:
    """
    YouTube 인기 급상승 동영상 리스트를 반환하는 MCP Tool
    """
    # FastMCP는 동기 함수만 받으므로 내부에서 asyncio 실행
    result = asyncio.run(get_trending_videos(max_results))
    return result

@mcp.tool(name="youtube_music")
def youtube_music(max_results: int = 3) -> str:
    """
    YouTube 인기 음악 리스트를 반환하는 MCP Tool
    """
    # FastMCP는 동기 함수만 받으므로 내부에서 asyncio 실행
    result = asyncio.run(get_trending_music_videos(max_results))
    return result

# 기존 예제 tool (원하면 유지)
@mcp.tool(name="calculator")
def calculator(operation: str, numbers: list[int]) -> float:
    if operation == "+":
        return sum(numbers)
    elif operation == "-":
        return numbers[0] - sum(numbers[1:])
    elif operation == "*":
        result = 1
        for n in numbers:
            result *= n
        return result
    elif operation == "/":
        result = numbers[0]
        for n in numbers[1:]:
            result /= n
        return result
    else:
        raise ValueError("지원하지 않는 연산입니다")

if __name__ == "__main__":
    mcp.run()
