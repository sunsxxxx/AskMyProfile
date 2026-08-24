from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Iterable
from typing import Any, Protocol

from redisvl.query.filter import FilterExpression, Tag

from app.models.chat import ToolSearchResult


logger = logging.getLogger(__name__)


class VectorStoreProtocol(Protocol):
    def similarity_search_with_score(
        self, query: str, *, k: int, filter: FilterExpression | None = None
    ) -> list[tuple[Any, float]]: ...


class RetrieverService:
    def __init__(self, vector_store: VectorStoreProtocol, *, top_k: int = 5) -> None:
        self.vector_store = vector_store
        self.top_k = top_k

    async def search(
        self,
        query: str,
        *,
        categories: Iterable[str],
        project_name: str | None = None,
        top_k: int | None = None,
    ) -> list[ToolSearchResult]:
        started = time.perf_counter()
        category_values = list(categories)
        category_filter = Tag("category") == category_values
        expression: FilterExpression = category_filter
        if project_name:
            expression = expression & (Tag("project") == project_name)
        rows = await asyncio.to_thread(
            self.vector_store.similarity_search_with_score,
            query,
            k=top_k or self.top_k,
            filter=expression,
        )
        logger.info(
            "retriever_complete categories=%s rows=%d duration_ms=%d",
            ",".join(category_values),
            len(rows),
            int((time.perf_counter() - started) * 1000),
        )
        return [
            ToolSearchResult(
                content=document.page_content,
                source=str(document.metadata.get("source", "")),
                category=str(document.metadata.get("category", "")),
                title=str(document.metadata.get("title", "")),
                section=str(document.metadata.get("section", "")),
                metadata={
                    key: value
                    for key, value in document.metadata.items()
                    if key not in {"source", "category", "title", "section"}
                },
                score=float(score) if score is not None else None,
            )
            for document, score in rows
        ]
