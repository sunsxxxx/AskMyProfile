from __future__ import annotations

from langchain_community.embeddings import DashScopeEmbeddings

from app.core.config import Settings


def create_embeddings(settings: Settings) -> DashScopeEmbeddings:
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")
    return DashScopeEmbeddings(
        model=settings.embedding_model,
        dashscope_api_key=settings.dashscope_api_key,
    )

