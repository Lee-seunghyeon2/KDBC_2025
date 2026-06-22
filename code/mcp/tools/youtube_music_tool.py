"""인기 급상승 영상 중 음악 관련 콘텐츠를 필터링하는 Tool입니다."""

from __future__ import annotations

from typing import Any

from .youtube_trend_tool import get_trending_videos

MUSIC_KEYWORDS = [
    "뮤직", "mv", "m/v", "노래", "음악", "song", "music", "official", "live", "ost",
    "playlist", "팝송", "pop", "힙합", "댄스", "발라드", "r&b", "k-pop", "케이팝",
    "앨범", "audio", "mix", "remix", "가사", "lyric", "studio",
]


def is_music_video(title: str) -> bool:
    """원본의 제목 키워드 기반 음악 영상 필터링 규칙입니다."""
    normalized = title.lower()
    return any(keyword in normalized for keyword in MUSIC_KEYWORDS)


def get_trending_music_videos(max_results: int = 5, region_code: str = "KR") -> dict[str, Any]:
    """인기 급상승 영상에서 음악 관련 영상만 골라 반환합니다.

    YouTube mostPopular API는 한 요청에 최대 50개를 제공하므로, 공개 버전은 한 페이지에서 필터링합니다.
    """
    request_size = min(max(int(max_results) * 5, 20), 50)
    result = get_trending_videos(max_results=request_size, region_code=region_code)
    if result.get("status") != "ok":
        return result
    music_videos = [video for video in result.get("videos", []) if is_music_video(video.get("title", ""))]
    if not music_videos:
        return {"status": "error", "message": "인기 급상승 목록에서 음악 관련 영상을 찾지 못했습니다.", "videos": []}
    return {"status": "ok", "videos": music_videos[:max_results]}
