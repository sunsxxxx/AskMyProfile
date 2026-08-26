from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.prompts import (
    AGENT_WORK_PROMPT,
    FINAL_ANSWER_PROMPT,
    PUBLIC_PROGRESS_PROMPT,
    SYSTEM_PROMPT,
)
from app.agent.tools import build_tools
from app.core.config import Settings
from app.github.client import GitHubClient
from app.rag.retriever import RetrieverService


def build_graph(
    settings: Settings,
    retriever: RetrieverService,
    github: GitHubClient,
    checkpointer: Any,
) -> Any:
    tools = build_tools(retriever, github)
    model_options: dict[str, Any] = {}
    if settings.llm_reasoning_effort:
        model_options["reasoning_effort"] = settings.llm_reasoning_effort

    model = ChatOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
        streaming=True,
        temperature=0.2,
        max_retries=2,
        **model_options,
    )
    tool_model = model.bind_tools(tools)

    async def agent(state: MessagesState) -> dict[str, Any]:
        response = await tool_model.ainvoke(
            [
                SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{AGENT_WORK_PROMPT}"),
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    async def answer(state: MessagesState) -> dict[str, Any]:
        response = await model.ainvoke(
            [
                SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{FINAL_ANSWER_PROMPT}"),
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    async def progress(state: MessagesState) -> dict[str, Any]:
        response = await model.ainvoke(
            [
                SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{PUBLIC_PROGRESS_PROMPT}"),
                *state["messages"],
            ]
        )
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_node("progress", progress)
    builder.add_node("answer", answer)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", "__end__": "answer"})
    builder.add_edge("tools", "progress")
    builder.add_edge("progress", "agent")
    builder.add_edge("answer", END)
    return builder.compile(checkpointer=checkpointer)
