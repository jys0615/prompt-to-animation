import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.generation import CutImage, CutVideo, GenerationCut, GenerationScene, GenerationStatus
from app.services import kie_service, openai_service

logger = logging.getLogger(__name__)


async def run_pipeline(scene_id: str) -> None:
    """Entry point for background generation pipeline."""
    async with AsyncSessionLocal() as db:
        try:
            await _run(db, scene_id)
        except Exception as exc:
            logger.exception("Pipeline failed for scene %s", scene_id)
            await _mark_scene_failed(db, scene_id, str(exc))


async def _run(db: AsyncSession, scene_id: str) -> None:
    scene = await db.get(GenerationScene, scene_id)
    if not scene:
        raise ValueError(f"Scene {scene_id} not found")

    scene.status = GenerationStatus.PROCESSING
    await db.commit()

    # 1. Generate scene structure via OpenAI
    try:
        if settings.mock_mode:
            spec = await openai_service.generate_scene_mock(scene.user_prompt)
        else:
            spec = await openai_service.generate_scene(scene.user_prompt)
    except Exception as exc:
        raise RuntimeError(f"OpenAI scene generation failed: {exc}") from exc

    scene.title = spec.title
    scene.scenario = spec.scenario
    await db.commit()

    # 2. Persist cuts
    cut_ids = []
    for idx, cut_spec in enumerate(spec.cuts):
        cut = GenerationCut(
            scene_id=scene_id,
            order=idx,
            image_prompt=cut_spec.image_prompt,
            video_prompt=cut_spec.video_prompt,
            duration_sec=cut_spec.duration_sec,
        )
        db.add(cut)
        cut_ids.append((cut, cut_spec.duration_sec))
    await db.commit()
    for cut, _ in cut_ids:
        await db.refresh(cut)

    # 3. Process all cuts in parallel — each cut gets its own DB session
    results = await asyncio.gather(
        *[_process_cut_isolated(cut.id, duration_sec) for cut, duration_sec in cut_ids],
        return_exceptions=True,
    )

    # 4. Check for failures
    failed = [r for r in results if isinstance(r, Exception)]
    if failed:
        raise RuntimeError(f"{len(failed)}/{len(results)} cuts failed: {failed[0]}")

    scene.status = GenerationStatus.COMPLETED
    await db.commit()
    logger.info("Scene %s completed (%d cuts)", scene_id, len(cut_ids))


async def _process_cut_isolated(cut_id: str, duration_sec: float) -> None:
    """각 cut은 독립 세션으로 병렬 처리."""
    async with AsyncSessionLocal() as db:
        cut = await db.get(GenerationCut, cut_id)
        if not cut:
            raise ValueError(f"Cut {cut_id} not found")
        await _process_cut(db, cut, duration_sec)


async def _process_cut(db: AsyncSession, cut: GenerationCut, duration_sec: float) -> None:
    cut.status = GenerationStatus.PROCESSING
    await db.commit()

    cut_image = CutImage(cut_id=cut.id)
    db.add(cut_image)
    await db.commit()
    await db.refresh(cut_image)

    # Generate image
    try:
        if settings.mock_mode:
            image_url = await kie_service.generate_image_mock(cut.image_prompt)
        else:
            image_url = await kie_service.generate_image(cut.image_prompt)

        cut_image.image_url = image_url
        cut_image.status = GenerationStatus.COMPLETED
        await db.commit()
        logger.info("Cut %s image completed: %s", cut.id, image_url)
    except Exception as exc:
        cut_image.status = GenerationStatus.FAILED
        cut_image.error_message = str(exc)
        cut.status = GenerationStatus.FAILED
        await db.commit()
        raise RuntimeError(f"Image generation failed for cut {cut.id}: {exc}") from exc

    # Generate video
    cut_video = CutVideo(cut_id=cut.id, cut_image_id=cut_image.id)
    db.add(cut_video)
    await db.commit()
    await db.refresh(cut_video)

    try:
        if settings.mock_mode:
            video_url = await kie_service.generate_video_mock(
                cut.video_prompt, image_url, duration_sec
            )
        else:
            video_url = await kie_service.generate_video(
                cut.video_prompt, image_url, duration_sec
            )

        cut_video.video_url = video_url
        cut_video.status = GenerationStatus.COMPLETED
        cut.status = GenerationStatus.COMPLETED
        await db.commit()
        logger.info("Cut %s video completed: %s", cut.id, video_url)
    except Exception as exc:
        cut_video.status = GenerationStatus.FAILED
        cut_video.error_message = str(exc)
        cut.status = GenerationStatus.FAILED
        await db.commit()
        raise RuntimeError(f"Video generation failed for cut {cut.id}: {exc}") from exc


async def _mark_scene_failed(db: AsyncSession, scene_id: str, message: str) -> None:
    scene = await db.get(GenerationScene, scene_id)
    if scene:
        scene.status = GenerationStatus.FAILED
        scene.error_message = message
        await db.commit()
