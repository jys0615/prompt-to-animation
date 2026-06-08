import asyncio
import logging
import uuid

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

KIE_COMPLETED_STATUSES = {"completed", "succeed", "success"}
KIE_FAILED_STATUSES = {"failed", "error"}


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.kie_api_key}",
        "Content-Type": "application/json",
    }


@retry(
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    stop=stop_after_attempt(settings.kie_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def _post(client: httpx.AsyncClient, url: str, payload: dict) -> dict:
    response = await client.post(url, json=payload, headers=_headers(), timeout=30.0)
    response.raise_for_status()
    return response.json()


async def _poll_task(client: httpx.AsyncClient, task_id: str) -> dict:
    """Poll until task completes or times out."""
    deadline = asyncio.get_event_loop().time() + settings.kie_poll_timeout_sec
    url = f"{settings.kie_base_url}/api/v1/jobs/recordInfo"

    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(
            url, params={"taskId": task_id}, headers=_headers(), timeout=15.0
        )
        resp.raise_for_status()
        data = resp.json()

        status = (
            data.get("data", {}).get("status", "")
            or data.get("data", {}).get("state", "")
        ).lower()

        logger.debug("Task %s status: %s", task_id, status)

        if status in KIE_COMPLETED_STATUSES:
            return data["data"]
        if status in KIE_FAILED_STATUSES:
            raise RuntimeError(f"Kie task {task_id} failed: {data}")

        await asyncio.sleep(settings.kie_poll_interval_sec)

    raise TimeoutError(f"Kie task {task_id} timed out after {settings.kie_poll_timeout_sec}s")


async def generate_image(image_prompt: str) -> str:
    """Submit image generation task and return image URL."""
    async with httpx.AsyncClient() as client:
        payload = {
            "model": settings.kie_image_model,
            "input": {
                "prompt": image_prompt,
                "output_format": "png",
                "aspect_ratio": "16:9",
            },
        }
        result = await _post(client, f"{settings.kie_base_url}/api/v1/jobs/createTask", payload)
        task_id = result["data"]["taskId"]
        logger.info("Image task created: %s", task_id)

        task_data = await _poll_task(client, task_id)
        image_url = (
            task_data.get("output", {}).get("image_url")
            or task_data.get("output", {}).get("images", [None])[0]
            or task_data.get("imageUrl")
        )
        if not image_url:
            raise RuntimeError(f"No image URL in task result: {task_data}")

        return image_url


async def generate_video(video_prompt: str, image_url: str, duration_sec: float) -> str:
    """Submit video generation task and return video URL."""
    duration = "10" if duration_sec >= 8 else "5"

    async with httpx.AsyncClient() as client:
        payload = {
            "model": settings.kie_video_model,
            "input": {
                "prompt": video_prompt,
                "image_urls": [image_url],
                "sound": False,
                "duration": duration,
            },
        }
        result = await _post(client, f"{settings.kie_base_url}/api/v1/jobs/createTask", payload)
        task_id = result["data"]["taskId"]
        logger.info("Video task created: %s", task_id)

        task_data = await _poll_task(client, task_id)
        video_url = (
            task_data.get("output", {}).get("video_url")
            or task_data.get("output", {}).get("videos", [None])[0]
            or task_data.get("videoUrl")
        )
        if not video_url:
            raise RuntimeError(f"No video URL in task result: {task_data}")

        return video_url


# --- Mock implementations ---

async def generate_image_mock(image_prompt: str) -> str:
    await asyncio.sleep(1)
    uid = uuid.uuid4().hex[:8]
    return f"https://mock.kie.ai/images/{uid}.png"


async def generate_video_mock(video_prompt: str, image_url: str, duration_sec: float) -> str:
    await asyncio.sleep(1)
    uid = uuid.uuid4().hex[:8]
    return f"https://mock.kie.ai/videos/{uid}.mp4"
