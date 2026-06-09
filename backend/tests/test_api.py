"""
FastAPI 엔드포인트 테스트 (TestClient, SQLite in-memory).
conftest.py에서 DATABASE_URL=sqlite+aiosqlite:///:memory: 설정 후 import.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_list_generations_empty():
    res = client.get("/api/generations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_start_generation_missing_prompt():
    res = client.post("/api/generations", json={})
    assert res.status_code == 422


def test_start_generation_empty_prompt():
    res = client.post("/api/generations", json={"prompt": ""})
    assert res.status_code == 422


def test_get_generation_not_found():
    res = client.get("/api/generations/nonexistent-id")
    assert res.status_code == 404


def test_start_generation_returns_pending():
    res = client.post("/api/generations", json={"prompt": "A sunset over the ocean"})
    assert res.status_code == 201
    body = res.json()
    assert body["status"] in ("pending", "processing")
    assert body["user_prompt"] == "A sunset over the ocean"
    assert "id" in body
