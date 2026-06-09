# Prompt-to-Animation

자연어 프롬프트를 입력하면 30초 내외의 애니메이션 영상을 생성해주는 풀스택 서비스입니다.

## 기술 스택

- **Frontend**: React + TypeScript (Vite)
- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL
- **Image Generation**: Kie API — Nano Banana (`google/nano-banana`)
- **Video Generation**: Kie API — Kling 2.6 (`kling-2.6/image-to-video`)
- **Scene Generation**: OpenAI GPT (`gpt-5.4-mini`)

---

## 실행 방법

### 사전 준비

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### 1. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일에 API 키를 입력합니다.

```env
OPENAI_API_KEY=sk-...
KIE_API_KEY=...
```

### 2. DB 실행 (Docker)

```bash
docker-compose up db -d
```

### 3. 백엔드 실행

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

백엔드: http://localhost:8000  
API 문서: http://localhost:8000/docs

### 4. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

프론트엔드: http://localhost:5173

### Docker Compose 전체 실행 (선택)

```bash
docker-compose up --build
```

---

## 환경변수 목록

| 변수 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | ✅ | - |
| `KIE_API_KEY` | Kie API 키 | ✅ | - |
| `DATABASE_URL` | PostgreSQL 연결 문자열 | - | `postgresql+asyncpg://postgres:postgres@localhost:5432/animation` |
| `MOCK_MODE` | `true` 설정 시 외부 API 호출 없이 더미 데이터 반환 | - | `false` |
| `OPENAI_MODEL` | 사용할 OpenAI 모델 ID | - | `gpt-5.4-mini` |
| `KIE_IMAGE_MODEL` | Kie 이미지 생성 모델 | - | `google/nano-banana` |
| `KIE_VIDEO_MODEL` | Kie 비디오 생성 모델 | - | `kling-2.6/image-to-video` |
| `KIE_POLL_INTERVAL_SEC` | Kie 작업 폴링 간격(초) | - | `5.0` |
| `KIE_POLL_TIMEOUT_SEC` | Kie 작업 타임아웃(초) | - | `300.0` |
| `KIE_MAX_RETRIES` | Kie API 실패 시 재시도 횟수 | - | `3` |

---

## 설계 설명

### 도메인 모델

```
UserPrompt
  └── GenerationScene (1:1)  ← OpenAI로 생성
        └── GenerationCut[] (1:n)
              ├── CutImage[] (1:n)  ← Kie Nano Banana
              └── CutVideo[] (1:n)  ← Kie Kling 2.6
```

### 생성 파이프라인

```
POST /api/generations
  │
  ├─ DB에 Scene 저장 (status: pending)
  └─ BackgroundTask 실행
        │
        ├─ OpenAI 호출 → title, scenario, cuts[] JSON 파싱
        ├─ Cuts DB 저장
        └─ 각 Cut 순차 처리
              ├─ Kie 이미지 생성 요청 → polling → image_url 저장
              └─ Kie 비디오 생성 요청 (image_url 사용) → polling → video_url 저장
```

- 생성은 **비동기 백그라운드**로 실행되어 즉시 응답 반환
- 프론트엔드는 **3초 간격 polling**으로 상태를 갱신
- Kie API 호출은 **tenacity** 라이브러리로 최대 3회 재시도
- `MOCK_MODE=true` 설정 시 외부 API 없이 더미 데이터로 전체 플로우 테스트 가능

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/generations` | 생성 시작 |
| `GET` | `/api/generations` | 생성 히스토리 목록 |
| `GET` | `/api/generations/{id}` | 생성 상태 및 결과 조회 |
| `POST` | `/api/generations/{id}/regenerate` | 재생성 |
| `GET` | `/health` | 헬스체크 |

### 에러 처리

| 상황 | 처리 방식 |
|------|-----------|
| OpenAI API 실패 | scene status → `failed`, error_message 저장 |
| Kie API 실패 | tenacity로 최대 3회 재시도 후 cut status → `failed` |
| Kie 타임아웃 (300초) | `TimeoutError` → cut/scene status → `failed` |
| 잘못된 요청 (빈 프롬프트 등) | FastAPI validation → 422 응답 |

---

## 테스트 / 검증 방법

### Mock mode로 전체 플로우 테스트

외부 API 키 없이 전체 플로우를 검증할 수 있습니다.

```bash
# .env에 설정
MOCK_MODE=true

# 백엔드 실행 후
curl -X POST http://localhost:8000/api/generations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A dragon flying over a medieval castle at night"}'

# 반환된 id로 상태 확인
curl http://localhost:8000/api/generations/{id}
```

### API 문서 (Swagger UI)

http://localhost:8000/docs 에서 모든 엔드포인트를 인터랙티브하게 테스트할 수 있습니다.

### 백엔드 유닛 테스트

```bash
cd backend
pytest tests/ -v
```

### 헬스체크

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### 프론트엔드 빌드 검증

```bash
cd frontend
npm run build
```
