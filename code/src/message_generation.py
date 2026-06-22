"""Gemma 기반 메시지 생성 모듈입니다.

원본의 텍스트 전용 Gemma 생성, LoRA adapter 적용, 생성 결과 추출 흐름을
환경변수와 비공개 adapter 경로를 사용하는 방식으로 정리했습니다.
"""

from __future__ import annotations

import os
from typing import Any


def load_text_model(
    model_source: str | None = None,
    adapter_path: str | None = None,
    hf_token: str | None = None,
) -> tuple[Any, Any]:
    """텍스트 생성용 Gemma와 선택적 LoRA adapter를 로드합니다."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    source = model_source or os.getenv("GEMMA_MODEL_PATH") or os.getenv("MODEL_ID", "google/gemma-3n-E2B-it")
    tokenizer = AutoTokenizer.from_pretrained(source, token=hf_token)
    model = AutoModelForCausalLM.from_pretrained(
        source,
        torch_dtype="auto",
        device_map="auto",
        token=hf_token,
    )

    resolved_adapter = adapter_path or os.getenv("LORA_ADAPTER_PATH")
    if resolved_adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, resolved_adapter)
    model.eval()
    return tokenizer, model


def generate_message(
    prompt: str,
    tokenizer: Any,
    model: Any,
    max_new_tokens: int = 80,
    temperature: float = 0.7,
    top_p: float = 0.8,
    do_sample: bool = True,
) -> str:
    """원본 `gemma_generate`의 입력 길이 이후 토큰만 추출하는 방식을 사용합니다."""
    import torch

    inputs = tokenizer(prompt, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {key: value.to(device) for key, value in inputs.items()}
    pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id
    input_length = inputs["input_ids"].shape[1]

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=do_sample,
            pad_token_id=pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_ids = outputs[0][input_length:]
    text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    if "<end_of_turn>" in text:
        text = text.split("<end_of_turn>", 1)[0].strip()
    return text


def generate_with_private_adapter(
    prompt: str,
    adapter_path: str | None = None,
    model_source: str | None = None,
    hf_token: str | None = None,
    **generation_kwargs: Any,
) -> str:
    """비공개 adapter를 보유한 로컬 환경에서만 실제 메시지를 생성하는 편의 함수입니다."""
    tokenizer, model = load_text_model(
        model_source=model_source,
        adapter_path=adapter_path,
        hf_token=hf_token,
    )
    return generate_message(prompt, tokenizer, model, **generation_kwargs)
