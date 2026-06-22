"""Gradio 기반 인터뷰형 프로토타입을 위한 보조 함수입니다."""

from __future__ import annotations

from typing import Any

from .homework_image_analyzer import analyze_with_fallbacks, percent_to_status
from .prompt_templates import build_improved_prompt

QUESTIONS = [
    "이름 또는 별명을 알려주세요.",
    "학년 또는 현재 학습 단계를 알려주세요.",
    "현재 공부 중인 과목을 알려주세요.",
    "오늘 숙제를 완료했나요? 예 / 아니오로 답해주세요.",
]


def parse_registration(text: str | None) -> bool | None:
    """완료 여부 응답을 True/False로 변환합니다."""
    if not text:
        return None
    normalized = text.strip().lower()
    positive = ("예", "네", "완료", "했", "yes", "y", "true")
    negative = ("아니", "못", "미완료", "no", "n", "false")
    if any(token in normalized for token in positive):
        return True
    if any(token in normalized for token in negative):
        return False
    return None


def build_student_profile(answers: list[str], interests: list[str] | None = None) -> dict[str, Any]:
    """인터뷰 답변을 메시지 파이프라인용 학생 프로필로 변환합니다."""
    completed = parse_registration(answers[3] if len(answers) > 3 else None)
    return {
        "name": answers[0] if len(answers) > 0 else "학생",
        "grade": answers[1] if len(answers) > 1 else "미입력",
        "subjects": answers[2] if len(answers) > 2 else "미입력",
        "registered": completed,
        "interests": interests or [],
    }


def build_ui_prompt(
    profile: dict[str, Any],
    attendance_text: str,
    tool_title: str,
    image_status: str | None = None,
) -> str:
    """UI에서 입력받은 정보로 개선 프롬프트를 구성합니다."""
    if image_status in {"완료", "미완료"}:
        status = image_status
    else:
        status = "완료" if profile.get("registered") else "미완료"
    return build_improved_prompt(
        homework_status=status,
        attendance_summary=attendance_text or "학습 인증 기록이 입력되지 않았습니다.",
        tool_result=tool_title or "외부 콘텐츠 정보를 사용하지 않음",
        interests=profile.get("interests", []),
    )


def analyze_uploaded_image(image: Any, processor: Any | None = None, model: Any | None = None) -> dict[str, Any]:
    """Gradio가 전달한 PIL 이미지를 분석합니다."""
    if image is None:
        return {"selected": {"status": "판단불가", "message": "이미지가 업로드되지 않았습니다."}, "attempts": []}
    return analyze_with_fallbacks(image, processor=processor, model=model)


def create_gradio_demo(
    generate_fn: Any,
    tool_title: str = "예시 인기 콘텐츠",
    processor: Any | None = None,
    model: Any | None = None,
):
    """원본의 인터뷰형 UI 흐름을 단순화해 재사용 가능한 Gradio Blocks로 만듭니다.

    `generate_fn(prompt)`에는 비공개 LoRA adapter를 적용한 생성 함수를 전달할 수 있습니다.
    모델을 전달하지 않으면 OCR/OpenCV 보조 분석만 수행합니다.
    """
    import gradio as gr

    def _run(name: str, grade: str, subject: str, completed: str, interests: str, attendance: str, image: Any):
        interest_list = [item.strip() for item in (interests or "").split(",") if item.strip()]
        profile = build_student_profile([name, grade, subject, completed], interests=interest_list)
        analysis = analyze_uploaded_image(image, processor=processor, model=model)
        selected = analysis.get("selected", {})
        prompt = build_ui_prompt(profile, attendance, tool_title, selected.get("status"))
        generated = generate_fn(prompt)
        return (
            f"숙제 분석 결과: {selected.get('status', '판단불가')}\n\n"
            f"생성 메시지:\n{generated}",
            prompt,
            analysis,
        )

    with gr.Blocks() as demo:
        gr.Markdown("# 개인화 학습 동기부여 메시지 프로토타입\n실제 학습자 정보와 이미지는 저장하지 않는 테스트용 UI입니다.")
        with gr.Row():
            with gr.Column():
                name = gr.Textbox(label="이름 또는 별명")
                grade = gr.Textbox(label="학년 또는 학습 단계")
                subject = gr.Textbox(label="과목")
                completed = gr.Radio(["예", "아니오"], label="숙제 완료 여부")
                interests = gr.Textbox(label="관심사 또는 좋아하는 가수", placeholder="예: 아이유, 에스파")
                attendance = gr.Textbox(label="누적 인증 정보", placeholder="예: 이번 주 5회차 인증, 누적 3회")
                image = gr.Image(type="pil", label="숙제 인증 이미지")
                run_button = gr.Button("메시지 생성")
            with gr.Column():
                output = gr.Textbox(label="결과", lines=8)
                prompt_output = gr.Textbox(label="생성 프롬프트", lines=12)
                analysis_output = gr.JSON(label="분석 상세 결과")
        run_button.click(_run, [name, grade, subject, completed, interests, attendance, image], [output, prompt_output, analysis_output])
    return demo
