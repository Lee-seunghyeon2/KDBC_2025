# KDBC 2025
## 소형 언어 모델 기반 개인화 학습 동기부여 메시지 생성 시스템

KDBC 2025에서 발표한 개인화 학습 동기부여 메시지 생성 프로젝트입니다. 학생의 숙제 인증 정보와 이미지 분석 결과, MCP Tool을 통해 수집한 외부 콘텐츠를 결합하고, LoRA로 미세조정한 Gemma 모델로 짧은 동기부여 메시지를 생성합니다.

## 핵심 시스템

```text
숙제 인증 이미지 ──> Gemma / OpenCV / OCR 기반 완료도 분석 ─┐
                                                              │
학생 프로필·누적 인증 정보 ────────────────────────────────────┼─> 프롬프트 구성 ─> LoRA Gemma ─> 동기부여 메시지
                                                              │
MCP Client ─> MCP Server ─> YouTube Tool ─────────────────────┘
```

- **이미지 기반 숙제 분석:** 멀티모달 Gemma로 숙제 완료 여부와 예상 완료율을 분석합니다. OpenCV 및 OCR 기반 보조 분석도 실험했습니다.
- **MCP Tool 연동:** MCP Server에 `youtube_trend`, `youtube_music`, `youtube_artist_search`, `calculator` Tool을 등록하고, MCP Client가 stdio 기반 요청·응답으로 Tool을 호출합니다.
- **개인화 메시지 생성:** 학생의 숙제 완료 여부, 누적 인증 정보, 외부 콘텐츠 결과를 프롬프트에 반영하여 LoRA Gemma가 한 줄 동기부여 메시지를 생성합니다.
- **확장 프로토타입:** 관심 가수 기반 콘텐츠 검색, 여러 관심사 결과 통합, Gradio 기반 인터뷰형 UI를 구현했습니다.

## 구현 범위

| 구분 | 내용 |
|---|---|
| 논문 핵심 파이프라인 | 이미지 기반 숙제 완료 여부 판단, `youtube_trend` Tool 호출, LoRA Gemma 메시지 생성 |
| MCP 확장 기능 | 인기 음악 영상 필터링, 관심 가수 기반 YouTube 검색, 계산 Tool |
| 이미지 분석 실험 | Gemma 멀티모달 분석, OpenCV 기반 채움 비율·원 검출, OCR 기반 완료율 보조 판독 |
| UI 프로토타입 | 학생 정보 입력, 숙제 이미지 업로드, 완료도 분석, 맞춤형 메시지 생성을 연결한 Gradio 데모 |

## 공개 범위

학습자 개인정보, 실제 숙제 인증 이미지, 실제 학습 데이터, API Key, Hugging Face Token, 모델 가중치 및 학습된 LoRA adapter는 포함하지 않습니다. 공개 코드는 원본 구현의 구조와 기능을 보존하되, 비식별 예시 데이터와 안전한 환경변수 설정 방식으로 정리했습니다.

## Repository Structure

```text
KDBC_2025/
├─ README.md
├─ .gitignore
├─ code/
│  ├─ README.md
│  ├─ requirements.txt
│  ├─ .env.example
│  ├─ notebooks/
│  │  ├─ 01_gemma_lora_training.ipynb
│  │  ├─ 02_multimodal_homework_analysis.ipynb
│  │  ├─ 03_mcp_tool_pipeline.ipynb
│  │  └─ 04_gradio_prototype.ipynb
│  ├─ mcp/
│  ├─ src/
│  └─ sample_data/
└─ docs/
   ├─ KDBC_2025_Presentation.pdf
   └─ KDBC_2025_Paper.pdf
```

## 자료

- [발표 자료 보기](./docs/KDBC_2025_Presentation.pdf)
- [논문 보기](./docs/KDBC_2025_Paper.pdf)

## Contribution

- 개인화 학습 동기부여 메시지 생성 시스템 설계 및 구현
- Gemma 기반 숙제 인증 이미지 분석 및 완료도 판별 실험
- MCP Server/Client와 YouTube Tool 연동 구현
- LoRA 기반 메시지 생성 모델 학습 및 비교 실험
- Gradio 기반 확장 프로토타입 구현
- KDBC 2025 발표 및 논문 공동 작성
