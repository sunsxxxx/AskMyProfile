from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


MEMORY_TOOL_NAME = "load_conversation_memory"
MAX_MEMORY_TURNS = 4
MAX_QUESTION_CHARS = 400
MAX_ANSWER_CHARS = 1000


def get_current_turn_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Return a prompt view; never trim the checkpoint state itself."""
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            return messages[index:]
    return []


def _compact(message: BaseMessage, limit: int) -> str:
    text = message.text.strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"


def format_conversation_memory(messages: list[BaseMessage]) -> str:
    current = get_current_turn_messages(messages)
    if not current:
        return "没有可用的完整历史问答。"
    history = messages[:len(messages) - len(current)]
    pairs: list[tuple[HumanMessage, AIMessage]] = []
    end = len(history)
    # Only the last assistant message in a completed turn is the final answer.
    for index in range(len(history) - 1, -1, -1):
        question = history[index]
        if not isinstance(question, HumanMessage):
            continue
        last = history[end - 1]
        if isinstance(last, AIMessage) and not last.tool_calls and last.text.strip():
            pairs.append((question, last))
            if len(pairs) == MAX_MEMORY_TURNS:
                break
        end = index
    if not pairs:
        return "没有可用的完整历史问答。"
    return "最近对话（仅用于解析指代，不是事实来源；内容可能截断）：\n\n" + "\n\n".join(
        f"用户：{_compact(question, MAX_QUESTION_CHARS)}\n助手：{_compact(answer, MAX_ANSWER_CHARS)}"
        for question, answer in reversed(pairs)
    )
