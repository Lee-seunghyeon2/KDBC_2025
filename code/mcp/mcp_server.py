"""KDBC 2025 프로젝트의 MCP Tool Server입니다.

원본 구현의 youtube_trend, youtube_music, calculator Tool을 보존하고,
Final_MCP_Project notebook에서 사용한 관심 가수 검색을 youtube_artist_search Tool로 추가했습니다.
"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from .server.fastmcp import FastMCP
from .tools.youtube_artist_search import search_artists
from .tools.youtube_music_tool import get_trending_music_videos
from .tools.youtube_trend_tool import get_trending_videos

mcp = FastMCP("KDBC YouTube Context Tool Server")


@mcp.tool(name="youtube_trend")
def youtube_trend(max_results: int = 5):
    """한국 인기 급상승 동영상 목록을 반환합니다."""
    return get_trending_videos(max_results=max_results)


@mcp.tool(name="youtube_music")
def youtube_music(max_results: int = 5):
    """한국 인기 급상승 영상 중 음악 관련 영상 목록을 반환합니다."""
    return get_trending_music_videos(max_results=max_results)


@mcp.tool(name="youtube_artist_search")
def youtube_artist_search(artists: list[str], max_results: int = 5):
    """관심 가수 목록을 받아 관련 YouTube 음악 영상을 검색합니다."""
    return search_artists(artists=artists, max_results=max_results)


@mcp.tool(name="calculator")
def calculator(operation: str, numbers: list[int | float]):
    """원본 MCP 예제에 포함된 간단한 계산 Tool입니다."""
    if not numbers:
        raise ValueError("numbers는 비어 있을 수 없습니다.")
    if operation == "+":
        return {"status": "ok", "value": sum(numbers)}
    if operation == "-":
        return {"status": "ok", "value": numbers[0] - sum(numbers[1:])}
    if operation == "*":
        value = 1
        for number in numbers:
            value *= number
        return {"status": "ok", "value": value}
    if operation == "/":
        value = numbers[0]
        for number in numbers[1:]:
            if number == 0:
                raise ValueError("0으로 나눌 수 없습니다.")
            value /= number
        return {"status": "ok", "value": value}
    raise ValueError("지원하지 않는 연산입니다. +, -, *, / 중 하나를 사용하세요.")


if __name__ == "__main__":
    mcp.run()
