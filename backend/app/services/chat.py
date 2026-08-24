from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import HumanMessage, ToolMessage

from app.models.chat import SourceItem


logger = logging.getLogger(__name__)


class GraphChatService:
    def __init__(self, graph: Any) -> None:
        self.graph = graph

    async def stream(self, message: str, thread_id: str) -> AsyncIterator[tuple[str, Any]]:
        started = time.perf_counter()
        sources: dict[tuple[str, str, str], SourceItem] = {}
        config = {"configurable": {"thread_id": thread_id}}
        async for part in self.graph.astream(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            stream_mode=["messages", "updates"],
            version="v2",
        ):
            if part["type"] == "messages":
                chunk, metadata = part["data"]
                content = chunk.content
                if metadata.get("langgraph_node") == "agent" and isinstance(content, str) and content:
                    yield "token", content
            elif part["type"] == "updates":
                tool_update = part["data"].get("tools")
                if tool_update:
                    yield "status", "资料检索完成，正在组织回答..."
                    for source in self._sources_from_update(tool_update):
                        sources[(source.source, source.title, source.section)] = source
        yield "sources", [source.model_dump() for source in sources.values()]
        logger.info(
            "agent_complete sources=%d duration_ms=%d",
            len(sources),
            int((time.perf_counter() - started) * 1000),
        )

    @staticmethod
    def _sources_from_update(update: dict[str, Any]) -> list[SourceItem]:
        sources: list[SourceItem] = []
        for message in update.get("messages", []):
            if not isinstance(message, ToolMessage) or not isinstance(message.content, str):
                continue
            try:
                payload = json.loads(message.content)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, list):
                continue
            for item in payload:
                if not isinstance(item, dict) or not item.get("source"):
                    continue
                sources.append(
                    SourceItem(
                        source=str(item["source"]),
                        title=str(item.get("title", "资料")),
                        section=str(item.get("section", "")),
                        category=str(item.get("category", "")),
                    )
                )
        return sources
