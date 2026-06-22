"""Gemma가 Tool 호출 계획을 JSON으로 생성하는 실험 Client입니다.

원본 `main.py`의 흐름을 유지합니다.
1) 학생 맥락을 읽음
2) Gemma가 Tool 호출 JSON을 생성
3) MCP Client가 Tool을 호출
4) Tool 결과를 최종 메시지 프롬프트에 반영

기본 실행은 모델을 로드하지 않고, 지정한 Tool을 호출하는 구조만 확인합니다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .main_tool_client import call_tool, format_video_summary
from src.message_generation import generate_message, load_text_model
from src.prompt_templates import build_improved_prompt, build_tool_planning_prompt, parse_tool_plan


def read_profile(profile_path: str | None) -> dict[str, Any]:
    """학생 맥락 JSON을 읽습니다. 기본값은 비식별 sample_data입니다."""
    default_path = Path(__file__).resolve().parents[1] / "sample_data" / "sample_attendance.json"
    path = Path(profile_path) if profile_path else default_path
    return json.loads(path.read_text(encoding="utf-8"))


def build_default_plan(profile: dict[str, Any], tool_name: str) -> list[dict[str, Any]]:
    """모델을 로드하지 않을 때 사용할 안전한 기본 Tool 계획입니다."""
    interests = profile.get("student_profile", {}).get("interests", [])
    if tool_name == "youtube_artist_search" and interests:
        return [{"method": "youtube_artist_search", "parameters": {"artists": interests, "max_results": 5}}]
    return [{"method": tool_name, "parameters": {"max_results": 5}}]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gemma 기반 MCP Tool 계획 생성 실험")
    parser.add_argument("--profile", type=str, default=None)
    parser.add_argument("--tool", choices=["youtube_trend", "youtube_music", "youtube_artist_search"], default="youtube_trend")
    parser.add_argument("--generate-plan", action="store_true", help="Gemma를 실제로 로드해 Tool 호출 JSON을 생성합니다.")
    parser.add_argument("--generate-message", action="store_true", help="비공개 LoRA adapter로 최종 메시지를 생성합니다.")
    return parser.parse_args()


async def main_async() -> None:
    load_dotenv()
    args = parse_args()
    profile = read_profile(args.profile)

    if args.generate_plan:
        planner_prompt = build_tool_planning_prompt(profile)
        tokenizer, model = load_text_model(hf_token=os.getenv("HF_TOKEN"))
        raw_plan = generate_message(planner_prompt, tokenizer, model, max_new_tokens=120, do_sample=False)
        plan = parse_tool_plan(raw_plan)
        if not plan:
            print("Gemma 출력에서 Tool JSON을 추출하지 못해 기본 Tool 계획을 사용합니다.")
            plan = build_default_plan(profile, args.tool)
    else:
        plan = build_default_plan(profile, args.tool)

    summaries: list[str] = []
    tool_titles: list[str] = []
    for call in plan:
        method = call.get("method", args.tool)
        parameters = call.get("parameters", {})
        tools, result = await call_tool(method, parameters)
        summaries.append(format_video_summary(method, result))
        if result.get("status") == "ok" and result.get("videos"):
            tool_titles.append(result["videos"][0].get("title", "외부 콘텐츠"))

    print("\n".join(summaries))
    status = "완료" if profile.get("student_profile", {}).get("registered") else "미완료"
    attendance = profile.get("content", "학습 기록 없음")
    prompt = build_improved_prompt(status, attendance, tool_titles[0] if tool_titles else "외부 콘텐츠 없음", profile.get("student_profile", {}).get("interests", []))
    print("\n[최종 메시지 프롬프트]\n", prompt)

    if args.generate_message:
        final_tokenizer, final_model = load_text_model(
            adapter_path=os.getenv("LORA_ADAPTER_PATH"),
            hf_token=os.getenv("HF_TOKEN"),
        )
        print("\n[생성 메시지]\n", generate_message(prompt, final_tokenizer, final_model))


if __name__ == "__main__":
    asyncio.run(main_async())
