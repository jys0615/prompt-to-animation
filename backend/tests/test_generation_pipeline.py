"""
Mock mode 기반 생성 파이프라인 통합 테스트.
실제 DB 없이 SQLite in-memory로 실행합니다.
"""
import asyncio
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("KIE_API_KEY", "test")
os.environ.setdefault("MOCK_MODE", "true")

from app.core.database import Base
from app.models.generation import GenerationScene, GenerationStatus
from app.services.generation_pipeline import _run

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_pipeline_completes_in_mock_mode(db: AsyncSession, monkeypatch):
    # patch AsyncSessionLocal used inside pipeline
    from sqlalchemy.orm import sessionmaker as sm
    from app.services import generation_pipeline

    mock_factory = sm(db.bind, class_=AsyncSession, expire_on_commit=False)

    class _FakeCtx:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(generation_pipeline, "AsyncSessionLocal", lambda: _FakeCtx())

    scene = GenerationScene(user_prompt="A sunset over the ocean")
    db.add(scene)
    await db.commit()
    await db.refresh(scene)

    await _run(db, scene.id)

    await db.refresh(scene)
    assert scene.status == GenerationStatus.COMPLETED
    assert scene.title is not None
    assert len(scene.cuts) >= 1
    for cut in scene.cuts:
        assert cut.status == GenerationStatus.COMPLETED
        assert len(cut.images) == 1
        assert cut.images[0].image_url is not None
        assert len(cut.images[0].videos) == 1
        assert cut.images[0].videos[0].video_url is not None


@pytest.mark.asyncio
async def test_scene_fails_on_openai_error(db: AsyncSession, monkeypatch):
    from app.services import generation_pipeline, openai_service

    async def _fail(*a, **kw):
        raise RuntimeError("OpenAI unavailable")

    monkeypatch.setattr(openai_service, "generate_scene_mock", _fail)

    class _FakeCtx:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(generation_pipeline, "AsyncSessionLocal", lambda: _FakeCtx())

    scene = GenerationScene(user_prompt="test")
    db.add(scene)
    await db.commit()
    await db.refresh(scene)

    await generation_pipeline.run_pipeline.__wrapped__ if hasattr(
        generation_pipeline.run_pipeline, "__wrapped__"
    ) else None

    # run_pipeline catches exceptions and marks scene failed
    await generation_pipeline.run_pipeline(scene.id)
    await db.refresh(scene)
    assert scene.status == GenerationStatus.FAILED
    assert scene.error_message is not None
