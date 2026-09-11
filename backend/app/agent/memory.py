from langchain_core.messages import BaseMessage, HumanMessage


def get_current_turn_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Return the current run tool loop; selected QA lives in a separate state field."""
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            return messages[index:]
    return []
