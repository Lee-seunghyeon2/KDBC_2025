"""동기부여 메시지 학습 데이터와 프롬프트를 구성하는 모듈입니다.

원본 notebook의 칭찬·격려 템플릿, 250개씩의 합성 데이터 구성,
기본 프롬프트 및 개선 프롬프트 흐름을 공개 가능한 형태로 정리했습니다.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any, Iterable

PRAISE_TEMPLATES = [
    "오늘 집중해서 끝까지 해낸 모습이 정말 멋져요. 스스로 정한 목표를 해낸 힘을 믿어요.",
    "숙제를 완성한 만큼 오늘의 노력도 분명히 쌓였어요. 다음 단계도 너만의 속도로 이어가 봐요.",
    "어려운 과제도 끝까지 해낸 끈기가 인상적이에요. 지금의 자신감을 다음 학습에도 가져가요.",
    "한 문제씩 해결하며 만들어 낸 결과예요. 네가 선택한 노력 자체가 이미 큰 성취예요.",
    "오늘의 인증은 단순한 기록이 아니라 꾸준히 성장하고 있다는 증거예요. 정말 잘했어요.",
]

ENCOURAGEMENT_TEMPLATES = [
    "오늘 다 끝내지 못했어도 괜찮아요. 가장 쉬운 한 문제부터 시작하며 너의 리듬을 찾아봐요.",
    "잠시 멈춘 날도 성장의 과정이에요. 부담을 줄이고 할 수 있는 만큼 다시 이어가 봐요.",
    "아직 남은 과제가 있어도 너의 가능성은 그대로예요. 작은 시작이 다음 성취를 만들어요.",
    "완벽하지 않아도 괜찮아요. 스스로 선택한 한 걸음이 내일의 자신감을 키워 줄 거예요.",
    "힘든 날에는 속도를 늦춰도 돼요. 필요한 도움을 요청하고 다시 시작할 힘을 모아봐요.",
]


def build_synthetic_instruction_data(
    praise_count: int = 250,
    encouragement_count: int = 250,
    seed: int = 42,
) -> list[dict[str, str]]:
    """원본의 250개 칭찬·250개 격려 데이터 구성 방식을 재현합니다.

    실제 프로젝트에서는 GPT-5를 활용한 합성 문장과 템플릿을 함께 사용했습니다.
    공개 버전은 개인정보가 없는 템플릿 기반 예시만 생성합니다.
    """
    rng = random.Random(seed)
    records: list[dict[str, str]] = []

    for index in range(praise_count):
        records.append(
            {
                "type": "attendance",
                "content": f"이번 학습 챌린지 {index % 30 + 1}회차 인증 (누적 {index % 30 + 1}회 인증)",
                "complete": "1",
                "response": rng.choice(PRAISE_TEMPLATES),
            }
        )

    for index in range(encouragement_count):
        records.append(
            {
                "type": "attendance",
                "content": f"이번 학습 챌린지 {index % 30 + 1}회차 인증 (누적 {index % 30 + 1}회 인증)",
                "complete": "0",
                "response": rng.choice(ENCOURAGEMENT_TEMPLATES),
            }
        )

    rng.shuffle(records)
    return records


def to_instruction_pairs(records: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """원본의 입력·출력 instruction tuning 형식으로 변환합니다."""
    pairs: list[dict[str, str]] = []
    for record in records:
        complete = record.get("complete") == "1"
        pairs.append(
            {
                "input": (
                    f"{'숙제를 완료한' if complete else '숙제를 완료하지 못한'} "
                    f"학생에게 한 줄 동기부여 메시지를 생성하세요. "
                    f"학습 기록: {record.get('content', '')}"
                ),
                "output": record.get("response", ""),
            }
        )
    return pairs


def format_instruction_pair(pair: dict[str, str]) -> str:
    """Gemma instruction tuning에 사용한 대화 형식 문자열을 만듭니다."""
    return (
        "<start_of_turn>user\n"
        f"{pair['input']}"
        "<end_of_turn>\n"
        "<start_of_turn>model\n"
        f"{pair['output']}"
        "<end_of_turn>"
    )


def locate_model_answer_start(input_ids: list[int], tokenizer: Any) -> int:
    """두 번째 turn marker 이후의 모델 응답 구간만 loss에 사용하기 위한 시작점을 찾습니다."""
    start_token_id = tokenizer.convert_tokens_to_ids("<start_of_turn>")
    positions = [idx for idx, token_id in enumerate(input_ids) if token_id == start_token_id]
    if len(positions) >= 2:
        return positions[1]
    return 0


def tokenize_instruction_example(example: dict[str, str], tokenizer: Any, max_length: int = 128) -> dict[str, list[int]]:
    """원본의 max_length=128, 모델 응답 구간 label masking 방식을 정리합니다."""
    text = format_instruction_pair(example)
    encoded = tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=max_length,
    )
    input_ids = list(encoded["input_ids"])
    answer_start = locate_model_answer_start(input_ids, tokenizer)
    labels = [-100] * answer_start + input_ids[answer_start:]

    if "attention_mask" in encoded:
        labels = [token if mask else -100 for token, mask in zip(labels, encoded["attention_mask"])]
    encoded["labels"] = labels
    return encoded


def build_baseline_prompt(
    homework_status: str,
    attendance_summary: str,
    tool_result: str,
) -> str:
    """초기 구현에서 사용한 30단어 이내 한 줄 메시지 프롬프트입니다."""
    direction = "칭찬" if homework_status == "완료" else "격려"
    return f"""<start_of_turn>user
숙제 {homework_status} 학생에게 한 줄 동기부여 메시지를 생성하세요.
[학습 기록] {attendance_summary}
[도구 결과] {tool_result}
[가이드라인]
1. 도구 결과를 메시지에 자연스럽게 연결하세요.
2. 숙제 완료이면 칭찬, 미완료이면 격려를 사용하세요.
3. 자기결정성 이론에 따라 자율성·유능감·관계성을 북돋으세요.
4. 따뜻하고 유머러스한 말투로, 30단어 이내 한 문장으로 작성하세요.
[메시지 방향] {direction}
<end_of_turn>
<start_of_turn>model
"""


def build_improved_prompt(
    homework_status: str,
    attendance_summary: str,
    tool_result: str,
    interests: Iterable[str] | None = None,
) -> str:
    """논문 후반의 개선 프롬프트: 안심 → 칭찬/격려 → 참여 유도 구조입니다."""
    interest_text = ", ".join(interests or []) or "입력되지 않음"
    middle_direction = "구체적인 성과를 칭찬" if homework_status == "완료" else "부담을 줄이는 격려"
    return f"""<start_of_turn>user
학생 맞춤형 학습 동기부여 메시지를 작성하세요.
[숙제 상태] {homework_status}
[누적 학습 기록] {attendance_summary}
[관심사] {interest_text}
[외부 콘텐츠] {tool_result}
[작성 규칙]
- 외부 콘텐츠를 학생의 학습 상황과 자연스럽게 연결하세요.
- 3단계 구조를 지키세요: 안심 → {middle_direction} → 다음 학습 참여 유도.
- 자율성·유능감·관계성을 북돋는 표현을 포함하세요.
- 추상적 수식어를 과도하게 사용하지 말고, 20단어 이내 한 문장으로 작성하세요.
<end_of_turn>
<start_of_turn>model
"""


def build_tool_planning_prompt(user_context: dict[str, Any]) -> str:
    """원본 main.py의 Gemma JSON Tool 계획 생성 프롬프트를 일반화합니다."""
    context_text = json.dumps(user_context, ensure_ascii=False)
    return f"""<start_of_turn>user
아래 학생 맥락을 바탕으로 필요한 MCP Tool 호출 계획을 JSON만으로 작성하세요.

[학생 맥락]
{context_text}

[사용 가능한 Tool]
- youtube_trend: 한국 인기 급상승 영상 조회. parameters: {{"max_results": 5}}
- youtube_music: 인기 영상 중 음악 관련 영상 조회. parameters: {{"max_results": 5}}
- youtube_artist_search: 관심 가수 검색. parameters: {{"artists": ["가수명"], "max_results": 5}}
- calculator: 간단한 계산. parameters: {{"operation": "+", "numbers": [1, 2]}}

예시:
{{"method": "youtube_trend", "parameters": {{"max_results": 5}}}}
또는 여러 호출:
[{{"method": "youtube_trend", "parameters": {{"max_results": 5}}}}, {{"method": "youtube_music", "parameters": {{"max_results": 5}}}}]

설명 없이 JSON 객체 또는 JSON 배열만 출력하세요.
<end_of_turn>
<start_of_turn>model
"""


def parse_tool_plan(text: str) -> list[dict[str, Any]]:
    """Gemma 출력에서 JSON Tool 호출 계획을 추출합니다."""
    candidates = re.findall(r"\[[\s\S]*?\]|\{[\s\S]*?\}", text)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            parsed = [parsed]
        if isinstance(parsed, list) and all(isinstance(item, dict) and "method" in item for item in parsed):
            return parsed
    return []
