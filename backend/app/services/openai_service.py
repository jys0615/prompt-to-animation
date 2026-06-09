import json
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


class CutSpec(BaseModel):
    image_prompt: str
    video_prompt: str
    duration_sec: float = 5.0


class SceneSpec(BaseModel):
    title: str
    scenario: str
    cuts: list[CutSpec]


SYSTEM_PROMPT = """You are an animation director. Convert the user's natural language prompt into a structured animation scene.

Return a JSON object with:
- title: short title for the animation (max 60 chars)
- scenario: brief narrative description (max 300 chars)
- cuts: array of EXACTLY 3 cuts, each with:
  - image_prompt: detailed prompt for image generation (English, max 200 chars)
  - video_prompt: motion description for video generation (English, max 200 chars)
  - duration_sec: duration in seconds (5 or 10)

You MUST generate exactly 3 cuts. Total duration should be around 30 seconds.
Respond ONLY with valid JSON, no extra text."""


async def generate_scene(user_prompt: str) -> SceneSpec:
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    logger.info("Calling OpenAI to generate scene for prompt: %s", user_prompt[:80])

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    raw = response.choices[0].message.content
    logger.info("OpenAI response received")

    data = json.loads(raw)
    return SceneSpec(**data)


async def generate_scene_mock(user_prompt: str) -> SceneSpec:
    return SceneSpec(
        title="Mock Animation",
        scenario="A mock animation scene for testing purposes.",
        cuts=[
            CutSpec(
                image_prompt="A serene sunset over the ocean, golden light, photorealistic",
                video_prompt="Camera slowly pans right, waves gently moving",
                duration_sec=5.0,
            ),
            CutSpec(
                image_prompt="A lone lighthouse on rocky cliffs, dramatic sky, cinematic",
                video_prompt="Zoom in slowly on the lighthouse, clouds moving in background",
                duration_sec=5.0,
            ),
            CutSpec(
                image_prompt="Stars reflected on calm ocean surface, night sky, ethereal",
                video_prompt="Slow upward tilt revealing the starry sky",
                duration_sec=5.0,
            ),
        ],
    )
