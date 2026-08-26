from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agent.graph import _prepare_final_answer_messages
from app.agent.prompts import FINAL_ANSWER_REQUEST


def test_final_answer_input_excludes_current_planner_control_message():
    question = HumanMessage(content="介绍一下你做过的项目")
    tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "search_project",
                "args": {"query": "项目"},
                "id": "call-project",
                "type": "tool_call",
            }
        ],
    )
    tool_result = ToolMessage(
        content='[{"source":"projects/example.md"}]',
        tool_call_id="call-project",
        name="search_project",
    )
    planner_control = AIMessage(content="资料准备完成", id="planner-control")

    prompt_messages, removed_message = _prepare_final_answer_messages(
        [question, tool_call, tool_result, planner_control]
    )

    assert removed_message is planner_control
    assert planner_control not in prompt_messages
    assert question in prompt_messages
    assert tool_call in prompt_messages
    assert tool_result in prompt_messages
    assert isinstance(prompt_messages[0], SystemMessage)
    assert isinstance(prompt_messages[-1], HumanMessage)
    assert prompt_messages[-1].content == FINAL_ANSWER_REQUEST


def test_final_answer_request_is_last_for_no_tool_questions():
    question = HumanMessage(content="什么是 Redis？")
    planner_control = AIMessage(content="资料准备完成", id="planner-control")

    prompt_messages, removed_message = _prepare_final_answer_messages(
        [question, planner_control]
    )

    assert removed_message is planner_control
    assert [message.content for message in prompt_messages[1:]] == [
        "什么是 Redis？",
        FINAL_ANSWER_REQUEST,
    ]


def test_previous_answer_history_is_preserved():
    previous_question = HumanMessage(content="介绍项目")
    previous_answer = AIMessage(content="我做过一个面试助手项目。")
    current_question = HumanMessage(content="为什么用了 Redis？")
    planner_control = AIMessage(content="资料准备完成", id="planner-control")

    prompt_messages, _ = _prepare_final_answer_messages(
        [previous_question, previous_answer, current_question, planner_control]
    )

    assert previous_answer in prompt_messages
    assert current_question in prompt_messages
    assert planner_control not in prompt_messages
