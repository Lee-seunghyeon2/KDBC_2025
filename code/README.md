# 코드 실행 안내

이 폴더는 KDBC 2025 프로젝트의 원본 구현을 공개 가능한 형태로 재구성한 코드입니다. 원본의 핵심 기능인 LoRA 학습, 멀티모달 숙제 이미지 분석, MCP Server/Client 기반 YouTube Tool 호출, 관심사 검색, Gradio 인터페이스를 유지했습니다.

## 실행 전 준비

```bash
cd code
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

`.env.example`을 복사해 `.env`를 만든 뒤, 필요한 값만 로컬에서 설정합니다.

```bash
# Windows PowerShell
Copy-Item .env.example .env
# macOS / Linux
# cp .env.example .env
```

- `YOUTUBE_API_KEY`: 실시간 YouTube Tool 호출에 필요합니다.
- `HF_TOKEN`: Gemma 접근 권한이 필요한 환경에서만 사용합니다.
- `GEMMA_MODEL_PATH`: 이미 내려받은 로컬 Gemma 모델이 있을 때 지정합니다.
- `LORA_ADAPTER_PATH`: 비공개 LoRA adapter를 보유한 경우에만 지정합니다.

## Notebook 구성

| 파일 | 목적 |
|---|---|
| `01_gemma_lora_training.ipynb` | 원본의 500개 instruction tuning 데이터 생성, LoRA 설정, 토큰화, Trainer 학습 흐름 |
| `02_multimodal_homework_analysis.ipynb` | Gemma 멀티모달 분석, OpenCV, OCR 기반 숙제 완료도 분석 실험 |
| `03_mcp_tool_pipeline.ipynb` | MCP Server/Client, 인기 영상·음악 영상·관심 가수 검색 Tool, Tool 결과 기반 프롬프트 구성 |
| `04_gradio_prototype.ipynb` | 학생 정보 인터뷰, 숙제 이미지 업로드, 분석 및 메시지 생성을 연결한 Gradio 프로토타입 |

## MCP 실행 예시

```bash
# code 폴더에서 실행
python -m mcp.main_tool_client --tool youtube_trend --max-results 5
python -m mcp.main_tool_client --tool youtube_music --max-results 5
python -m mcp.main_tool_client --tool youtube_artist_search --artists "아이유 에스파" --max-results 5
```

`main_gemma_client.py`는 Gemma가 Tool 호출 계획을 JSON 형태로 생성하도록 실험한 원본 흐름을 정리한 파일입니다. 실제 모델을 로드하려면 GPU 환경, 모델 접근 권한, 필요한 환경변수가 필요합니다.

## 공개 제한

실제 학습자 프로필, 숙제 인증 이미지, 원본 학습 데이터, API Key, 모델 가중치, LoRA adapter, checkpoint는 이 repository에 포함하지 않습니다. 예시 JSON과 코드는 구조를 설명하기 위한 비식별 버전입니다.
