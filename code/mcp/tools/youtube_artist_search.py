"""관심 가수 기반 YouTube 콘텐츠 검색 Tool입니다.

원본 notebook의 `get_artist_music_videos`와 여러 관심사 결과를 합치는 로직을 모듈화했습니다.
"""

from __future__ import annotations

import os
from typing import Any, Iterable

import requests

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def get_artist_music_videos(artist_name: str, max_results: int = 10, order_by: str = "relevance") -> dict[str, Any]:
    """가수명과 음악 관련 검색어를 사용해 YouTube 영상을 찾습니다."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "YOUTUBE_API_KEY가 설정되지 않았습니다.", "videos": []}

    params = {
        "part": "snippet",
        "q": f"{artist_name} official music",
        "type": "video",
        "maxResults": max(1, min(int(max_results), 50)),
        "order": order_by,
        "key": api_key,
    }
    try:
        response = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {"status": "error", "message": f"YouTube 검색 요청 실패: {exc}", "videos": []}

    videos = []
    for item in response.json().get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId")
        if not video_id:
            continue
        videos.append(
            {
                "artist": artist_name,
                "title": snippet.get("title", "제목 없음"),
                "channel": snippet.get("channelTitle", "채널 정보 없음"),
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail_url": (snippet.get("thumbnails", {}).get("high") or snippet.get("thumbnails", {}).get("default") or {}).get("url"),
            }
        )
    return {"status": "ok", "artist": artist_name, "videos": videos}


def search_artists(artists: Iterable[str], max_results: int = 10) -> dict[str, Any]:
    """여러 관심 가수의 검색 결과를 합치고 영상 URL 기준으로 중복을 제거합니다."""
    combined: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_urls: set[str] = set()
    for artist in artists:
        artist = artist.strip()
        if not artist:
            continue
        result = get_artist_music_videos(artist, max_results=max_results)
        if result.get("status") != "ok":
            errors.append(f"{artist}: {result.get('message', '알 수 없는 오류')}")
            continue
        for video in result.get("videos", []):
            url = video.get("video_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                combined.append(video)
    if not combined:
        return {"status": "error", "message": "; ".join(errors) or "검색 결과가 없습니다.", "videos": []}
    return {"status": "ok", "videos": combined, "errors": errors}
