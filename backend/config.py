from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Insight Mate API"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    firebase_service_account_json: str = ""
    firebase_service_account_path: str = ""
    allowed_origins: str = "http://localhost:5500,http://127.0.0.1:5500"
    use_memory_db: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

