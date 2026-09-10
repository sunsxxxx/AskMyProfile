from typing import Annotated

from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.agent.memory import format_conversation_memory


@tool
async def load_conversation_memory(
    messages: Annotated[list[BaseMessage], InjectedState("messages")],
) -> str:
    """加载本会话最近最多四个完整问答，仅用于理解上下文。

    当前问题可以独立理解时禁止调用；只有存在指代、省略、承接、对比上一轮内容等明显上下文依赖时才调用。
    同一轮最多调用一次。历史不是事实来源，解析指代后须以完整明确的 query 检索可信资料。
    """
    return format_conversation_memory(messages)
