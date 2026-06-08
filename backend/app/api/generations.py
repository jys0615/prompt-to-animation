import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.generation import CutImage, GenerationCut, GenerationScene, GenerationStatus
from app.schemas.generation import (
    GenerationListItem,
    GenerationResponse,
    StartGenerationRequest,
)
from app.services.generation_pipeline import run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/generations", tags=["generations"])

_SCENE_WITH_RELATIONS = (
    selectinload(GenerationScene.cuts)
    .selectinload(GenerationCut.images)
    .selectinload(CutImage.videos)
)


@router.post("", response_model=GenerationResponse, status_code=201)
async def start_generation(
    body: StartGenerationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    scene = GenerationScene(user_prompt=body.prompt)
    db.add(scene)
    await db.commit()
    await db.refresh(scene)

    background_tasks.add_task(run_pipeline, scene.id)
    logger.info("Generation started: scene_id=%s", scene.id)

    stmt = (
        select(GenerationScene)
        .where(GenerationScene.id == scene.id)
        .options(_SCENE_WITH_RELATIONS)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("", response_model=list[GenerationListItem])
async def list_generations(db: AsyncSession = Depends(get_db)):
    stmt = select(GenerationScene).order_by(GenerationScene.created_at.desc())
    rows = await db.execute(stmt)
    return rows.scalars().all()


@router.get("/{scene_id}", response_model=GenerationResponse)
async def get_generation(scene_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(GenerationScene)
        .where(GenerationScene.id == scene_id)
        .options(_SCENE_WITH_RELATIONS)
    )
    result = await db.execute(stmt)
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Generation not found")
    return scene


@router.post("/{scene_id}/regenerate", response_model=GenerationResponse, status_code=202)
async def regenerate(
    scene_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    scene = await db.get(GenerationScene, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Generation not found")
    if scene.status == GenerationStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="Generation already in progress")

    scene.status = GenerationStatus.PENDING
    scene.error_message = None
    await db.commit()

    background_tasks.add_task(run_pipeline, scene.id)
    return scene
