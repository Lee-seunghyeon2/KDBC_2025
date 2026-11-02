import os
import requests
import json  # 🔹 추가

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_TREND_URL = "https://www.googleapis.com/youtube/v3/videos"

async def get_trending_music_videos(max_results: int = 50000):
    if not YOUTUBE_API_KEY:
        return {
            "status": "error",
            "message": "❌ YOUTUBE_API_KEY가 설정되지 않았습니다."
        }
    all_results = []
    next_page_token = None
    current_results_count = 0

    # YouTube API는 한 번에 최대 50개 결과를 반환.
    # 더 많은 결과를 위해 여러 번 호출.

    api_max_results_per_call = 50
    try:
        while current_results_count < max_results: # 요청된 max_results에 도달할 때까지 반복
            params = {
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": "KR",
                "maxResults": api_max_results_per_call, # <<< API의 실제 최대값인 50으로 설정
                "key": YOUTUBE_API_KEY
            }

            if next_page_token:
                params["pageToken"] = next_page_token # 다음 페이지 토큰이 있으면 추가

            res = requests.get(YOUTUBE_TREND_URL, params=params)

            if res.status_code != 200:
                return {
                    "status": "error",
                    "message": f"❌ API 요청 실패: {res.text}"
                }

            data = res.json()
            items = data.get("items", [])

            if not items: # 더 이상 결과가 없으면 반복 중단
                break

            music_keywords = [
                "뮤직", "MV", "엠비", "노래", "음악", "송", "사운드", "트랙",
                "Music", "Official", "Live", "OST", "라이브", "보이스",
                "M/V", "플레이리스트", "playlist", "팝송", "pop",
                "힙합", "댄스", "발라드", "R&B", "알앤비", "k-pop", "케이팝", "밴드", "싱글", "앨범",
                "audio", "mix", "remix", "리믹스", "가사", "lyric", "studio"
            ]

            # 현재 페이지의 아이템들을 필터링하고 전체 결과에 추가
            for item in items:
                if any(kw.lower() in item["snippet"]["title"].lower() for kw in music_keywords):
                    snippet = item["snippet"]
                    stats = item.get("statistics", {})
                    video_id = item["id"]

                    all_results.append({
                        "title": snippet["title"],
                        "channel": snippet["channelTitle"],
                        "view_count": stats.get("viewCount", "0")
                    })
                    current_results_count = len(all_results)
                    if current_results_count >= max_results: # 필요한 만큼 결과를 모았으면 중단
                        break

            next_page_token = data.get("nextPageToken") # 다음 페이지 토큰 가져오기
            if not next_page_token: # 더 이상 다음 페이지가 없으면 반복 중단
                break

        if not all_results:
            return {
                "status": "error",
                "message": "⚠️ 인기 음악 영상이 없습니다."
            }

        return {
            "status": "ok",
            "videos": all_results[:max_results] # 요청된 max_results에 맞춰 슬라이싱
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }