from types import SimpleNamespace

from app.services.chat import GraphChatService


class FakeGraph:
    async def astream(self, *_args, **_kwargs):
        yield {
            "type": "messages",
            "data": (SimpleNamespace(content="不应展示的工具决策内容"), {"langgraph_node": "agent"}),
        }
        yield {
            "type": "messages",
            "data": (SimpleNamespace(content="正在检索"), {"langgraph_node": "progress"}),
        }
        yield {
            "type": "messages",
            "data": (SimpleNamespace(content="最终回答"), {"langgraph_node": "answer"}),
        }


async def test_stream_routes_progress_and_answer_content_separately():
    events = [event async for event in GraphChatService(FakeGraph()).stream("问题", "thread")]

    assert ("intermediate", "正在检索") in events
    assert ("token", "最终回答") in events
    assert all("不应展示" not in content for _, content in events if isinstance(content, str))
    assert ("token", "正在检索") not in events
