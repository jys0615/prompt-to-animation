from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    kie_api_key: str
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/animation"
    mock_mode: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
