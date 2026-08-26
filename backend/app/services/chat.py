from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import HumanMessage, ToolMessage

from app.models.chat import SourceItem


logger = logging.getLogger(__name__)


TOOL_DISPLAY_NAMES: dict[str, str] = {
    "search_resume": "简历资料检索",
    "search_project": "项目资料检索",
    "search_skill": "技能资料检索",
    "search_github": "GitHub 公开仓库检索",
}


class GraphChatService:
    def __init__(self, graph: Any) -> None:
        self.graph = graph

    async def stream(self, message: str, thread_id: str) -> AsyncIterator[tuple[str, Any]]:
        started = time.perf_counter()
        sources: dict[tuple[str, str, str], SourceItem] = {}
        tool_names_by_call_id: dict[str, str] = {}
        announced_tool_calls: set[str] = set()
        announced_tool_completions: set[str] = set()
        used_tools = False
        final_stage_announced = False
        config = {"configurable": {"thread_id": thread_id}}
        yield "intermediate", f"收到问题：{message}"
        async for part in self.graph.astream(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            stream_mode=["messages", "updates"],
            version="v2",
        ):
            if part["type"] == "messages":
                chunk, metadata = part["data"]
                content = chunk.content
                node = metadata.get("langgraph_node")
                if node == "answer" and isinstance(content, str) and content:
                    if not final_stage_announced:
                        for trace in self._final_stage_traces(used_tools):
                            yield "intermediate", trace
                        final_stage_announced = True
                    yield "token", content
            elif part["type"] == "updates":
                update = part["data"]
                agent_update = update.get("agent")
                if agent_update:
                    tool_calls = self._tool_calls_from_update(agent_update)
                    if tool_calls:
                        used_tools = True
                        for call_id, tool_name in tool_calls:
                            if call_id:
                                tool_names_by_call_id[call_id] = tool_name
                                if call_id in announced_tool_calls:
                                    continue
                                announced_tool_calls.add(call_id)
                            yield "intermediate", self._tool_started_trace(tool_name)
                    elif not final_stage_announced:
                        for trace in self._final_stage_traces(used_tools):
                            yield "intermediate", trace
                        final_stage_announced = True

                tool_update = update.get("tools")
                if tool_update:
                    for call_id, tool_name in self._completed_tools_from_update(
                        tool_update, tool_names_by_call_id
                    ):
                        if call_id:
                            if call_id in announced_tool_completions:
                                continue
                            announced_tool_completions.add(call_id)
                        yield "intermediate", self._tool_completed_trace(tool_name)
                    for source in self._sources_from_update(tool_update):
                        sources[(source.source, source.title, source.section)] = source
        yield "sources", [source.model_dump() for source in sources.values()]
        logger.info(
            "agent_complete sources=%d duration_ms=%d",
            len(sources),
            int((time.perf_counter() - started) * 1000),
        )

    @staticmethod
    def _tool_calls_from_update(update: dict[str, Any]) -> list[tuple[str, str]]:
        calls: list[tuple[str, str]] = []
        for message in update.get("messages", []):
            for call in getattr(message, "tool_calls", []) or []:
                if not isinstance(call, dict):
                    continue
                name = call.get("name")
                if not isinstance(name, str) or not name:
                    continue
                call_id = call.get("id")
                calls.append((call_id if isinstance(call_id, str) else "", name))
        return calls

    @staticmethod
    def _completed_tools_from_update(
        update: dict[str, Any], tool_names_by_call_id: dict[str, str]
    ) -> list[tuple[str, str]]:
        completed: list[tuple[str, str]] = []
        for message in update.get("messages", []):
            if not isinstance(message, ToolMessage):
                continue
            call_id = message.tool_call_id
            name = message.name or tool_names_by_call_id.get(call_id, "")
            completed.append((call_id, name))
        return completed

    @staticmethod
    def _tool_label(tool_name: str) -> str:
        return TOOL_DISPLAY_NAMES.get(tool_name, "资料处理")

    @classmethod
    def _tool_started_trace(cls, tool_name: str) -> str:
        label = cls._tool_label(tool_name)
        return f"正在调用{label}工具 {tool_name}。" if tool_name else f"正在调用{label}工具。"

    @classmethod
    def _tool_completed_trace(cls, tool_name: str) -> str:
        return f"{cls._tool_label(tool_name)}完成。"

    @staticmethod
    def _final_stage_traces(used_tools: bool) -> tuple[str, ...]:
        if used_tools:
            return ("资料准备完成，正在生成最终回答。",)
        return ("Agent 判断该问题无需检索个人资料。", "正在生成最终回答。")

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
