import requests
import os
import json  # 🔹 추가

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_TREND_URL = "https://www.googleapis.com/youtube/v3/videos"

async def get_trending_videos(max_results: int = 3):
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": "KR",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(YOUTUBE_TREND_URL, params=params)

    if response.status_code != 200:
        return json.dumps({"status": "error", "message": response.text}, ensure_ascii=False)  # 🔹 직렬화

    items = response.json().get("items", [])
    results = []

    for item in items:
        video_id = item["id"]
        snippet = item["snippet"]
        stats = item["statistics"]
        results.append({
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail_url": snippet["thumbnails"]["high"]["url"],
            "view_count": stats.get("viewCount", "0")
        })

    return {  # 🔹 여기도 직렬화
        "status": "ok",
        "videos": results
    }
