from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"))
    openai_api_key: str
    kie_api_key: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/animation"
    mock_mode: bool = False

    openai_model: str = "gpt-4o-mini"
    kie_base_url: str = "https://api.kie.ai"
    kie_image_model: str = "google/nano-banana"
    kie_video_model: str = "kling-2.6/image-to-video"

    kie_poll_interval_sec: float = 5.0
    kie_poll_timeout_sec: float = 300.0
    kie_max_retries: int = 3



settings = Settings()
