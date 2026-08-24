from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1)
    thread_id: UUID

    @field_validator("message")
    @classmethod
    def reject_blank_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value


class SourceItem(BaseModel):
    title: str
    source: str
    section: str = ""
    category: str = ""


class ToolSearchResult(BaseModel):
    content: str
    source: str
    category: str
    title: str
    section: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None
