# Prompt-to-Animation — AI Coding Agent Instructions

## Project Overview
Full-stack service that converts natural language prompts into short animated videos (~30s).
- **Frontend**: React + TypeScript (Vite), http://localhost:5173
- **Backend**: FastAPI (Python 3.12), http://localhost:8000
- **DB**: PostgreSQL (via docker-compose)

## Domain Model
```
user prompt → GenerationScene (1:1)
GenerationScene → GenerationCut[] (1:n)
GenerationCut → CutImage[] (1:n)         ← Kie API, google/nano-banana
GenerationCut + CutImage → CutVideo[] (1:n)  ← Kie API, kling-2.6/image-to-video
```

## Key Rules
- API keys (OPENAI_API_KEY, KIE_API_KEY) must NEVER appear in frontend code
- All external API keys are backend environment variables only
- `MOCK_MODE=true` enables full flow testing without real API calls
- Image generation must complete before video generation starts (sequential per cut)
- All infra dependencies (DB) are in docker-compose.yml — do NOT add other services

## Project Structure
```
/
├── backend/
│   ├── app/
│   │   ├── api/generations.py       # REST endpoints
│   │   ├── core/config.py           # Settings (pydantic-settings)
│   │   ├── core/database.py         # SQLAlchemy async engine
│   │   ├── models/generation.py     # ORM models
│   │   ├── schemas/generation.py    # Pydantic schemas
│   │   ├── services/
│   │   │   ├── openai_service.py    # GPT scene generation
│   │   │   ├── kie_service.py       # Kie image/video + polling + retry
│   │   │   └── generation_pipeline.py  # Background orchestration
│   │   └── main.py
│   ├── tests/
│   │   ├── conftest.py              # Sets env vars + SQLite DB for tests
│   │   ├── test_api.py              # Endpoint tests (TestClient)
│   │   └── test_generation_pipeline.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/generations.ts       # API client
│       ├── components/              # PromptForm, CutCard, GenerationDetail, etc.
│       ├── hooks/usePolling.ts      # 3s polling hook
│       └── types/generation.ts     # TypeScript types
├── docker-compose.yml               # PostgreSQL + backend + frontend
├── .env.example
└── CLAUDE.md
```

## Generation Pipeline
```
POST /api/generations
  → DB: Scene(status=pending)
  → BackgroundTask: run_pipeline(scene_id)
      1. OpenAI GPT → scene JSON (title, scenario, cuts[])
      2. For each cut (sequential):
         a. Kie POST createTask (google/nano-banana) → poll recordInfo → image_url
         b. Kie POST createTask (kling-2.6/image-to-video) → poll recordInfo → video_url
      3. Scene status → completed
```

## API Endpoints
```
POST   /api/generations              # start generation
GET    /api/generations              # list history
GET    /api/generations/{id}         # get status + result (used for polling)
POST   /api/generations/{id}/regenerate  # regenerate
GET    /health                       # health check
```

## Status Values
`pending` → `processing` → `completed` | `failed`

## Kie API
- Base URL: `https://api.kie.ai`
- Create task: `POST /api/v1/jobs/createTask`
- Poll status: `GET /api/v1/jobs/recordInfo?taskId={taskId}`
- Auth: `Authorization: Bearer {KIE_API_KEY}`

## Running Tests
```bash
cd backend
pytest tests/ -v
```
Tests use SQLite in-memory (via conftest.py env override) — no DB setup needed.

## Running Locally
```bash
# DB
docker-compose up db -d

# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev
```
