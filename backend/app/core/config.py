from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = ""
    llm_reasoning_effort: str = ""
    llm_timeout_seconds: float = Field(default=60, gt=0)

    dashscope_api_key: str = ""
    embedding_model: str = "text-embedding-v3"

    redis_url: str = "redis://localhost:6379"
    redis_connect_timeout_seconds: float = Field(default=3, gt=0)
    redis_index_name: str = "interview_knowledge"

    github_username: str = ""
    github_token: str = ""
    github_cache_ttl: int = Field(default=600, ge=300, le=600)
    github_timeout_seconds: float = Field(default=10, gt=0)

    frontend_origin: str = "http://localhost:5173"
    trusted_proxies: Annotated[tuple[str, ...], NoDecode] = ()

    rate_limit_max_requests: int = Field(default=5, gt=0)
    rate_limit_window_seconds: int = Field(default=60, gt=0)
    rate_limit_key_ttl_seconds: int = Field(default=90, gt=0)
    max_message_length: int = Field(default=2000, ge=1, le=10000)
    retriever_top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("trusted_proxies", mode="before")
    @classmethod
    def parse_trusted_proxies(cls, value: object) -> tuple[str, ...]:
        if value is None or value == "":
            return ()
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return tuple(value)  # type: ignore[arg-type]

    @field_validator("frontend_origin")
    @classmethod
    def reject_wildcard_origin(cls, value: str) -> str:
        if value.strip() == "*":
            raise ValueError("FRONTEND_ORIGIN must be an explicit origin")
        return value.rstrip("/")

    @property
    def knowledge_dir(self) -> Path:
        return Path(__file__).resolve().parents[3] / "knowledge"

    def missing_chat_settings(self) -> list[str]:
        required = {
            "LLM_API_KEY": self.llm_api_key,
            "LLM_MODEL": self.llm_model,
            "DASHSCOPE_API_KEY": self.dashscope_api_key,
        }
        return [name for name, value in required.items() if not value]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
