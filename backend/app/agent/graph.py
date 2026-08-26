from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.prompts import (
    AGENT_WORK_PROMPT,
    FINAL_ANSWER_PROMPT,
    FINAL_ANSWER_REQUEST,
    SYSTEM_PROMPT,
)
from app.agent.tools import build_tools
from app.core.config import Settings
from app.github.client import GitHubClient
from app.rag.retriever import RetrieverService


def _prepare_final_answer_messages(
    messages: list[BaseMessage],
) -> tuple[list[BaseMessage], AIMessage | None]:
    planner_message: AIMessage | None = None
    conversation = messages
    if messages and isinstance(messages[-1], AIMessage) and not messages[-1].tool_calls:
        planner_message = messages[-1]
        conversation = messages[:-1]

    return (
        [
            SystemMessage(content=f"{SYSTEM_PROMPT}\n\n{FINAL_ANSWER_PROMPT}"),
            *conversation,
            HumanMessage(content=FINAL_ANSWER_REQUEST),
        ],
        planner_message,
    )


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
        prompt_messages, planner_message = _prepare_final_answer_messages(state["messages"])
        response = await model.ainvoke(prompt_messages)
        message_updates: list[BaseMessage] = []
        if planner_message is not None and planner_message.id:
            message_updates.append(RemoveMessage(id=planner_message.id))
        message_updates.append(response)
        return {"messages": message_updates}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_node("answer", answer)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", "__end__": "answer"})
    builder.add_edge("tools", "agent")
    builder.add_edge("answer", END)
    return builder.compile(checkpointer=checkpointer)
