import asyncio
import json
import logging
import uuid

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

KIE_COMPLETED_STATUSES = {"completed", "succeed", "success"}
KIE_FAILED_STATUSES = {"failed", "error"}

# 앱 레벨 싱글턴 클라이언트 — TCP 커넥션 재사용으로 매 호출 handshake 비용 제거
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


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


def _extract_url(task_data: dict) -> str | None:
    """실제 Kie API 응답에서 미디어 URL을 추출한다.

    알려진 응답 형태:
    - resultJson: '{"resultUrls": ["https://..."]}'
    - output.image_url / output.video_url
    - output.images[0] / output.videos[0]
    - imageUrl / videoUrl (최상위)
    """
    # 1) resultJson 파싱 (Nano Banana 실제 응답)
    result_json_str = task_data.get("resultJson")
    if result_json_str:
        try:
            result_json = json.loads(result_json_str)
            urls = (
                result_json.get("resultUrls")
                or result_json.get("videoUrls")
                or result_json.get("imageUrls")
            )
            if urls and len(urls) > 0:
                return urls[0]
        except (json.JSONDecodeError, TypeError):
            pass

    # 2) output 객체
    output = task_data.get("output", {}) or {}
    url = (
        output.get("image_url")
        or output.get("video_url")
        or (output.get("images") or [None])[0]
        or (output.get("videos") or [None])[0]
    )
    if url:
        return url

    # 3) 최상위 필드
    return task_data.get("imageUrl") or task_data.get("videoUrl")


async def _poll_task(client: httpx.AsyncClient, task_id: str) -> dict:
    """Poll until task completes or times out."""
    deadline = asyncio.get_event_loop().time() + settings.kie_poll_timeout_sec
    url = f"{settings.kie_base_url}/api/v1/jobs/recordInfo"

    while asyncio.get_event_loop().time() < deadline:
        resp = await client.get(
            url, params={"taskId": task_id}, headers=_headers(), timeout=15.0
        )
        resp.raise_for_status()
        raw = resp.json()

        # 응답이 {"data": {...}} 또는 직접 task 객체인 경우 모두 처리
        task_data = raw.get("data", raw)
        if isinstance(task_data, dict) and "taskId" not in task_data:
            task_data = raw

        status = (
            task_data.get("state", "")
            or task_data.get("status", "")
        ).lower()

        logger.debug("Task %s status: %s", task_id, status)

        if status in KIE_COMPLETED_STATUSES:
            return task_data
        if status in KIE_FAILED_STATUSES:
            raise RuntimeError(f"Kie task {task_id} failed: {raw}")

        await asyncio.sleep(settings.kie_poll_interval_sec)

    raise TimeoutError(f"Kie task {task_id} timed out after {settings.kie_poll_timeout_sec}s")


async def generate_image(image_prompt: str) -> str:
    """Submit image generation task and return image URL."""
    client = get_client()
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
    image_url = _extract_url(task_data)
    if not image_url:
        raise RuntimeError(f"No image URL in task result: {task_data}")

    return image_url


async def generate_video(video_prompt: str, image_url: str, duration_sec: float) -> str:
    """Submit video generation task and return video URL."""
    client = get_client()
    duration = "10" if duration_sec >= 8 else "5"
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
    video_url = _extract_url(task_data)
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
