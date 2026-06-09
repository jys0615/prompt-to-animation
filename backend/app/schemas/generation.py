from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.generation import GenerationStatus


class StartGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="자연어 사용자 입력")


class CutVideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: GenerationStatus
    video_url: str | None


class CutImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: GenerationStatus
    image_url: str | None
    videos: list[CutVideoResponse] = []


class CutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order: int
    image_prompt: str
    video_prompt: str
    duration_sec: float
    status: GenerationStatus
    images: list[CutImageResponse] = []


class GenerationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_prompt: str
    title: str | None
    scenario: str | None
    status: GenerationStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    cuts: list[CutResponse] = []


class GenerationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_prompt: str
    title: str | None
    status: GenerationStatus
    created_at: datetime
