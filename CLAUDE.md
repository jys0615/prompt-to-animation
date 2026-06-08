# Prompt-to-Animation — AI Coding Agent Instructions

## Project Overview
Full-stack service that converts natural language prompts into short animated videos (~30s).
- **Frontend**: React + TypeScript (Vite)
- **Backend**: FastAPI (Python 3.12)
- **DB**: PostgreSQL (via docker-compose)

## Domain Model
```
user prompt → GenerationScene (1:1)
GenerationScene → GenerationCut[] (1:n)
GenerationCut → CutImage[] (1:n)   ← Kie API, Nano banana model
GenerationCut + CutImage → CutVideo[] (1:n)  ← Kie API, kling-2.6 model
```

## Key Rules
- API keys (OPENAI_API_KEY, KIE_API_KEY) must NEVER appear in frontend code
- All external API keys are managed as backend environment variables only
- Use `MOCK_MODE=true` for local development without real API calls
- Image generation must complete before video generation starts (sequential per cut)
- All infrastructure dependencies (DB) are in docker-compose.yml; do NOT add other infra services

## Backend Structure
```
backend/
  app/
    api/         # FastAPI routers
    core/        # config, database
    models/      # SQLAlchemy ORM models
    schemas/     # Pydantic request/response schemas
    services/    # business logic (openai, kie, generation pipeline)
  tests/
```

## Status Flow
```
PENDING → PROCESSING → COMPLETED
                     → FAILED
```

## Generation Pipeline (per scene)
1. Call OpenAI GPT to parse user prompt → scene JSON (title, scenario, cuts[])
2. For each cut sequentially:
   a. POST Kie image generation (Nano banana)
   b. Poll until image COMPLETED
   c. POST Kie video generation (kling-2.6) using completed image
   d. Poll until video COMPLETED
3. Update scene status to COMPLETED when all cuts done

## API Endpoints
- `POST /api/generations` — start generation
- `GET /api/generations/{id}` — get status + result
- `GET /api/generations` — list history
- `POST /api/generations/{id}/regenerate` — regenerate (optional)

## Environment Variables
See `.env.example` for all required variables.

## Running Locally
```bash
# 1. Start DB
docker-compose up db -d

# 2. Backend
cd backend
pip install -r requirements.txt
cp ../.env.example .env  # fill in keys
uvicorn app.main:app --reload

# 3. Frontend
cd frontend
npm install
npm run dev
```
