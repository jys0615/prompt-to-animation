"""
Mock mode 기반 생성 파이프라인 통합 테스트.
"""
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker

from app.core.database import Base
from app.models.generation import CutImage, GenerationCut, GenerationScene, GenerationStatus
from app.services.generation_pipeline import _run, run_pipeline

TEST_DB_URL = "sqlite+aiosqlite:///./test_pipeline.sqlite3"


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session._test_factory = factory  # 병렬 처리용 팩토리 참조 저장
        yield session

    await engine.dispose()

    import os
    if os.path.exists("./test_pipeline.sqlite3"):
        os.remove("./test_pipeline.sqlite3")


async def _load_scene(db: AsyncSession, scene_id: str) -> GenerationScene:
    stmt = (
        select(GenerationScene)
        .where(GenerationScene.id == scene_id)
        .options(
            selectinload(GenerationScene.cuts)
            .selectinload(GenerationCut.images)
            .selectinload(CutImage.videos)
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@pytest.mark.asyncio
async def test_pipeline_completes_in_mock_mode(db: AsyncSession, monkeypatch):
    from app.services import generation_pipeline

    factory = db._test_factory

    class _FakeCtx:
        def __init__(self):
            self._session = None
        async def __aenter__(self):
            self._session = factory()
            return await self._session.__aenter__()
        async def __aexit__(self, *args):
            await self._session.__aexit__(*args)

    monkeypatch.setattr(generation_pipeline, "AsyncSessionLocal", _FakeCtx)

    scene = GenerationScene(user_prompt="A sunset over the ocean")
    db.add(scene)
    await db.commit()
    await db.refresh(scene)

    await _run(db, scene.id)

    scene = await _load_scene(db, scene.id)
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

    monkeypatch.setattr(generation_pipeline, "AsyncSessionLocal", _FakeCtx)

    scene = GenerationScene(user_prompt="test")
    db.add(scene)
    await db.commit()
    await db.refresh(scene)

    await run_pipeline(scene.id)

    scene = await _load_scene(db, scene.id)
    assert scene.status == GenerationStatus.FAILED
    assert scene.error_message is not None
