"""숙제 인증 이미지 분석 모듈입니다.

원본 구현의 세 가지 접근을 보존합니다.
1) Gemma-3n-E2B-it 멀티모달 분석
2) OpenCV 기반 채움 비율·원 검출 실험
3) OCR 기반 완료율 보조 판독

실제 학습자 이미지와 사설 저장소 URL은 public repository에 포함하지 않습니다.
"""

from __future__ import annotations

import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def build_attendance_image_url(attendance_id: str, filename: str, base_url: str | None = None) -> str:
    """사설 환경에서 사용한 출석 이미지 URL 조합 방식을 일반화합니다.

    공개 버전은 base_url을 강제하지 않습니다. 실제 서비스의 주소는 `.env`로만 제공하세요.
    """
    resolved_base_url = base_url or os.getenv("ATTENDANCE_IMAGE_BASE_URL")
    if not resolved_base_url:
        raise ValueError("ATTENDANCE_IMAGE_BASE_URL이 설정되지 않았습니다. 공개 예시에서는 로컬 이미지 경로를 사용하세요.")
    stem = Path(filename).stem
    return f"{resolved_base_url.rstrip('/')}/{attendance_id}/{stem}.jpg"


def load_image(image_source: str | Path | Image.Image, timeout: int = 20) -> Image.Image:
    """로컬 경로, URL, PIL 이미지를 RGB PIL 이미지로 반환합니다."""
    if isinstance(image_source, Image.Image):
        return ImageOps.exif_transpose(image_source).convert("RGB")

    source_text = str(image_source)
    if source_text.startswith(("http://", "https://")):
        response = requests.get(source_text, timeout=timeout)
        response.raise_for_status()
        return ImageOps.exif_transpose(Image.open(BytesIO(response.content))).convert("RGB")

    return ImageOps.exif_transpose(Image.open(source_text)).convert("RGB")


def prepare_image_for_model(image: Image.Image, max_side: int = 1536) -> Image.Image:
    """원본 Gradio 프로토타입의 EXIF 정리와 해상도 제한 방식을 반영합니다."""
    prepared = ImageOps.exif_transpose(image).convert("RGB")
    if max(prepared.size) > max_side:
        scale = max_side / max(prepared.size)
        prepared = prepared.resize(
            (int(prepared.width * scale), int(prepared.height * scale)),
            Image.Resampling.LANCZOS,
        )
    return prepared


def load_multimodal_gemma(
    model_source: str | None = None,
    hf_token: str | None = None,
) -> tuple[Any, Any]:
    """Gemma 멀티모달 processor와 model을 로드합니다.

    GPU 환경과 Gemma 접근 권한이 필요할 수 있습니다.
    """
    import torch
    from transformers import AutoProcessor, Gemma3nForConditionalGeneration

    source = model_source or os.getenv("GEMMA_MODEL_PATH") or os.getenv("MODEL_ID", "google/gemma-3n-E2B-it")
    processor = AutoProcessor.from_pretrained(source, token=hf_token)
    model = Gemma3nForConditionalGeneration.from_pretrained(
        source,
        torch_dtype="auto",
        device_map="auto",
        token=hf_token,
    ).eval()
    return processor, model


def _clean_model_text(text: str) -> str:
    if "<start_of_turn>model" in text:
        text = text.split("<start_of_turn>model", 1)[1]
    if "<end_of_turn>" in text:
        text = text.split("<end_of_turn>", 1)[0]
    return text.strip()


def analyze_with_gemma(
    image_source: str | Path | Image.Image,
    processor: Any,
    model: Any,
    prompt: str | None = None,
    max_new_tokens: int = 96,
) -> dict[str, Any]:
    """Gemma 멀티모달 모델로 숙제 완료도와 완료율을 분석합니다."""
    import torch

    image = prepare_image_for_model(load_image(image_source))
    instruction = prompt or (
        "이 숙제 인증 이미지를 분석하세요. 완료 여부를 완료 또는 미완료로 먼저 말하고, "
        "예상 완료율을 0~100%로 제시하세요. 풀이 흔적, 체크·동그라미·세모 표기를 근거로 짧게 설명하세요."
    )
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": instruction},
            ],
        }
    ]
    chat_text = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=[chat_text], images=[image], return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {key: value.to(device) for key, value in inputs.items()}
    input_length = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        outputs = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    generated = outputs[0][input_length:]
    text = _clean_model_text(processor.decode(generated, skip_special_tokens=True))
    percent = extract_completion_percent(text)
    status = percent_to_status(percent) if percent is not None else infer_status_from_text(text)
    return {"method": "gemma_multimodal", "status": status, "percent": percent, "raw_text": text}


def extract_completion_percent(text: str | None) -> int | None:
    """Gemma 또는 OCR 응답에서 0~100 범위의 퍼센트를 추출합니다."""
    if not text:
        return None
    matched = re.search(r"(100|[1-9]?\d)\s*%", text)
    if matched:
        return int(matched.group(1))
    numbers = re.findall(r"\b(100|[1-9]?\d)\b", text)
    for number in numbers:
        value = int(number)
        if 0 <= value <= 100:
            return value
    return None


def infer_status_from_text(text: str) -> str:
    """명시적인 퍼센트가 없는 경우 모델의 완료/미완료 표현을 보조적으로 해석합니다."""
    normalized = text.replace(" ", "")
    if "미완료" in normalized or "부분" in normalized or "아직" in normalized:
        return "미완료"
    if "완료" in normalized or "해결" in normalized:
        return "완료"
    return "판단불가"


def percent_to_status(percent: int | None, threshold: int = 70) -> str:
    """원본 UI의 완료율 임계값 판단을 일반화합니다."""
    if percent is None:
        return "판단불가"
    return "완료" if percent >= threshold else "미완료"


def analyze_with_opencv(
    image_source: str | Path | Image.Image,
    complete_fill_ratio: float = 40.0,
    partial_fill_ratio: float = 15.0,
) -> dict[str, Any]:
    """원본의 OpenCV 기반 채움 비율·Hough circle 실험을 정리합니다.

    이 방식은 이미지 양식과 조명에 민감한 실험적 보조 방법입니다.
    """
    import cv2

    image = load_image(image_source).convert("L")
    cv_image = np.array(image)
    _, binary = cv2.threshold(cv_image, 128, 255, cv2.THRESH_BINARY_INV)
    fill_ratio = float(np.mean(binary > 0) * 100)
    circles = cv2.HoughCircles(
        cv_image,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=50,
        param1=100,
        param2=50,
        minRadius=35,
        maxRadius=80,
    )
    circle_count = min(len(circles[0]), 20) if circles is not None else 0

    if fill_ratio > complete_fill_ratio or circle_count > 5:
        status = "완료"
    elif fill_ratio > partial_fill_ratio:
        status = "부분완료"
    else:
        status = "미완료"

    return {
        "method": "opencv_fill_ratio_and_circles",
        "status": status,
        "fill_ratio": round(fill_ratio, 2),
        "circle_count": int(circle_count),
    }


def analyze_with_ocr(image_source: str | Path | Image.Image) -> dict[str, Any]:
    """원본 UI의 OCR 기반 완료율 보조 판독 방식입니다."""
    try:
        import pytesseract
    except ImportError as exc:
        return {"method": "ocr", "status": "판단불가", "percent": None, "message": f"pytesseract를 설치하세요: {exc}"}

    image = load_image(image_source).convert("L")
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(1.5)
    text = pytesseract.image_to_string(image, lang="eng+kor")
    percent = extract_completion_percent(text)
    return {
        "method": "ocr",
        "status": percent_to_status(percent),
        "percent": percent,
        "raw_text": text.strip(),
    }


def analyze_with_fallbacks(
    image_source: str | Path | Image.Image,
    processor: Any | None = None,
    model: Any | None = None,
) -> dict[str, Any]:
    """Gemma → OCR → OpenCV 순서로 보조 분석을 수행합니다."""
    attempts: list[dict[str, Any]] = []
    if processor is not None and model is not None:
        gemma_result = analyze_with_gemma(image_source, processor, model)
        attempts.append(gemma_result)
        if gemma_result.get("status") != "판단불가":
            return {"selected": gemma_result, "attempts": attempts}

    ocr_result = analyze_with_ocr(image_source)
    attempts.append(ocr_result)
    if ocr_result.get("status") != "판단불가":
        return {"selected": ocr_result, "attempts": attempts}

    opencv_result = analyze_with_opencv(image_source)
    attempts.append(opencv_result)
    return {"selected": opencv_result, "attempts": attempts}
