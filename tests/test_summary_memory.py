from unittest.mock import Mock

from app.memory import (
    add_message,
    clear_session_memory,
    get_summary,
)

from app.memory_manager import (
    update_summary_if_needed,
)


def test_update_summary_when_history_exceeds_window(
    monkeypatch
):
    session_id = "test-summary-update"

    clear_session_memory(session_id)

    # 为了测试方便，这里只保留最近2轮
    max_turns = 2

    # 连续写入3轮对话
    for i in range(1, 4):

        add_message(
            session_id,
            "user",
            f"第{i}轮问题"
        )

        add_message(
            session_id,
            "assistant",
            f"第{i}轮回答"
        )

    mock_summarize_memory = Mock(
        return_value="这是生成的历史摘要"
    )

    monkeypatch.setattr(
        "app.memory_manager.summarize_memory",
        mock_summarize_memory
    )

    update_summary_if_needed(
        session_id=session_id,
        max_turns=max_turns
    )

    # 1. Summary 确实保存成功
    assert get_summary(session_id) == "这是生成的历史摘要"

    # 2. summarize_memory 只调用了一次
    mock_summarize_memory.assert_called_once()

    # 3. 查看 summarize_memory 真正收到的参数
    call = mock_summarize_memory.call_args

    old_summary = call.kwargs["old_summary"]
    messages = call.kwargs["messages"]

    # 第一次生成 Summary，所以旧 Summary 应该为空
    assert old_summary == ""

    # 只能总结已经滑出 Recent History 的第1轮
    assert messages == [
        {
            "role": "user",
            "content": "第1轮问题"
        },
        {
            "role": "assistant",
            "content": "第1轮回答"
        }
    ]

    clear_session_memory(session_id)

