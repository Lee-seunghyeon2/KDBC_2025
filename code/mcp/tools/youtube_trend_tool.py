"""YouTube 인기 급상승 영상 수집 Tool입니다."""

from __future__ import annotations

import os
from typing import Any

import requests

YOUTUBE_TREND_URL = "https://www.googleapis.com/youtube/v3/videos"


def get_trending_videos(max_results: int = 5, region_code: str = "KR") -> dict[str, Any]:
    """YouTube Data API v3에서 한국 인기 급상승 영상을 반환합니다."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "YOUTUBE_API_KEY가 설정되지 않았습니다.", "videos": []}

    max_results = max(1, min(int(max_results), 50))
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": max_results,
        "key": api_key,
    }
    try:
        response = requests.get(YOUTUBE_TREND_URL, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {"status": "error", "message": f"YouTube API 요청 실패: {exc}", "videos": []}

    videos = []
    for item in response.json().get("items", []):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        video_id = item.get("id", "")
        thumbnails = snippet.get("thumbnails", {})
        high_thumbnail = thumbnails.get("high") or thumbnails.get("default") or {}
        videos.append(
            {
                "title": snippet.get("title", "제목 없음"),
                "channel": snippet.get("channelTitle", "채널 정보 없음"),
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail_url": high_thumbnail.get("url"),
                "view_count": statistics.get("viewCount", "0"),
            }
        )
    return {"status": "ok", "videos": videos}
