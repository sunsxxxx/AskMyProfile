from __future__ import annotations

from typing import Any

from langchain_redis import RedisConfig, RedisVectorStore
from redis import Redis as SyncRedis
from redis.exceptions import ResponseError

from app.core.config import Settings


METADATA_SCHEMA = [
    {"name": "source", "type": "tag"},
    {"name": "path", "type": "tag"},
    {"name": "category", "type": "tag"},
    {"name": "title", "type": "tag"},
    {"name": "project", "type": "tag"},
    {"name": "section", "type": "tag"},
]


def create_vector_store(settings: Settings, embeddings: Any) -> RedisVectorStore:
    config = RedisConfig(
        index_name=settings.redis_index_name,
        redis_url=settings.redis_url,
        connection_args={
            "socket_connect_timeout": settings.redis_connect_timeout_seconds,
            "socket_timeout": settings.redis_connect_timeout_seconds,
        },
        distance_metric="COSINE",
        metadata_schema=METADATA_SCHEMA,
    )
    return RedisVectorStore(embeddings=embeddings, config=config)


def drop_application_index(settings: Settings) -> bool:
    """Drop only this application's search index and its indexed document keys."""
    client = SyncRedis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=settings.redis_connect_timeout_seconds,
        socket_timeout=settings.redis_connect_timeout_seconds,
    )
    try:
        client.execute_command("FT.DROPINDEX", settings.redis_index_name, "DD")
        return True
    except ResponseError as exc:
        if "Unknown Index name" in str(exc) or "no such index" in str(exc).lower():
            return False
        raise
    finally:
        client.close()
