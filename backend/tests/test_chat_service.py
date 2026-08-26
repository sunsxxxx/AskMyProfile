import json

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage

from app.services.chat import GraphChatService


class FakeGraph:
    def __init__(self, parts):
        self.parts = parts
        self.inputs = []

    async def astream(self, graph_input, **_kwargs):
        self.inputs.append(graph_input)
        for part in self.parts:
            yield part


def agent_update(*calls: tuple[str, str, dict]) -> dict:
    tool_calls = [
        {"name": name, "id": call_id, "args": args, "type": "tool_call"}
        for name, call_id, args in calls
    ]
    return {
        "type": "updates",
        "data": {"agent": {"messages": [AIMessage(content="", tool_calls=tool_calls)]}},
    }


def tools_update(*messages: ToolMessage) -> dict:
    return {"type": "updates", "data": {"tools": {"messages": list(messages)}}}


def node_message(node: str, content: str) -> dict:
    return {
        "type": "messages",
        "data": (AIMessageChunk(content=content), {"langgraph_node": node}),
    }


def tool_result(name: str, call_id: str, payload=None) -> ToolMessage:
    content = json.dumps(payload if payload is not None else [], ensure_ascii=False)
    return ToolMessage(content=content, tool_call_id=call_id, name=name)


async def collect(parts, message="用户问题"):
    graph = FakeGraph(parts)
    events = [event async for event in GraphChatService(graph).stream(message, "thread")]
    return graph, events


def event_values(events, event_name):
    return [data for event, data in events if event == event_name]


async def test_single_tool_trace_hides_arguments_and_result_content():
    source_payload = [
        {
            "source": "projects/interview-agent.md",
            "title": "面试助手",
            "section": "架构",
            "category": "project",
            "content": "不应进入公开轨迹的项目正文",
        }
    ]
    _, events = await collect(
        [
            agent_update(("search_project", "call-project", {"query": "敏感的完整查询参数"})),
            tools_update(tool_result("search_project", "call-project", source_payload)),
            agent_update(),
            node_message("agent", "不应展示的工具决策内容"),
            node_message("answer", "最终回答"),
        ],
        "介绍一下你做过的项目",
    )

    assert event_values(events, "intermediate") == [
        "收到问题：介绍一下你做过的项目",
        "正在调用项目资料检索工具 search_project。",
        "项目资料检索完成。",
        "资料准备完成，正在生成最终回答。",
    ]
    assert event_values(events, "token") == ["最终回答"]
    trace = "\n".join(event_values(events, "intermediate"))
    assert "敏感的完整查询参数" not in trace
    assert "不应进入公开轨迹的项目正文" not in trace
    assert "不应展示的工具决策内容" not in trace
    assert event_values(events, "sources") == [
        [
            {
                "source": "projects/interview-agent.md",
                "title": "面试助手",
                "section": "架构",
                "category": "project",
            }
        ]
    ]


async def test_multiple_tools_are_announced_once_and_sources_stay_deduplicated():
    source = {
        "source": "skills/redis.md",
        "title": "Redis",
        "section": "实践",
        "category": "skill",
    }
    calls = (
        ("search_skill", "call-skill", {"query": "Redis"}),
        ("search_project", "call-project", {"query": "Redis"}),
    )
    completions = (
        tool_result("search_skill", "call-skill", [source]),
        tool_result("search_project", "call-project", [source]),
    )
    _, events = await collect(
        [
            agent_update(*calls),
            agent_update(*calls),
            tools_update(*completions),
            tools_update(*completions),
            agent_update(),
            node_message("answer", "回答"),
        ]
    )

    traces = event_values(events, "intermediate")
    assert traces.count("正在调用技能资料检索工具 search_skill。") == 1
    assert traces.count("正在调用项目资料检索工具 search_project。") == 1
    assert traces.count("技能资料检索完成。") == 1
    assert traces.count("项目资料检索完成。") == 1
    assert len(event_values(events, "sources")) == 1
    assert len(event_values(events, "sources")[0]) == 1


async def test_no_tool_call_does_not_claim_that_retrieval_happened():
    _, events = await collect([agent_update(), node_message("answer", "Redis 是一种数据存储。")])

    traces = event_values(events, "intermediate")
    assert traces == [
        "收到问题：用户问题",
        "Agent 判断该问题无需检索个人资料。",
        "正在生成最终回答。",
    ]
    assert all("检索完成" not in trace and "正在调用" not in trace for trace in traces)
    assert event_values(events, "token") == ["Redis 是一种数据存储。"]


async def test_multiple_tool_rounds_preserve_real_execution_order():
    _, events = await collect(
        [
            agent_update(("search_project", "call-project", {"query": "项目"})),
            tools_update(tool_result("search_project", "call-project")),
            agent_update(("search_skill", "call-skill", {"query": "Redis"})),
            tools_update(tool_result("search_skill", "call-skill")),
            agent_update(),
            node_message("answer", "最终回答"),
        ]
    )

    assert event_values(events, "intermediate") == [
        "收到问题：用户问题",
        "正在调用项目资料检索工具 search_project。",
        "项目资料检索完成。",
        "正在调用技能资料检索工具 search_skill。",
        "技能资料检索完成。",
        "资料准备完成，正在生成最终回答。",
    ]


async def test_intermediate_is_not_added_to_graph_messages_state():
    graph, events = await collect(
        [
            agent_update(),
            node_message("progress", "旧 progress 正式答案"),
            node_message("answer", "唯一最终回答"),
        ]
    )

    assert len(graph.inputs) == 1
    messages = graph.inputs[0]["messages"]
    assert len(messages) == 1
    assert isinstance(messages[0], HumanMessage)
    assert messages[0].content == "用户问题"
    assert all("收到问题" not in item.content for item in messages)
    assert event_values(events, "token") == ["唯一最终回答"]
    assert "旧 progress 正式答案" not in event_values(events, "intermediate")
    assert ("token", "旧 progress 正式答案") not in events
