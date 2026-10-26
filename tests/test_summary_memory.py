from unittest.mock import Mock

from app.memory import (
    add_message,
    clear_session_memory,
    get_summary,
)

from app.memory_manager import (
    update_summary_if_needed,
)

# 给 Rolling Summary 增加基础自动化测试，验证旧消息摘要和摘要保存逻辑。
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

# 验证已经总结过的旧消息，下一次不会被重复总结。
def test_summary_does_not_repeat_old_messages(
    monkeypatch
):

    session_id = "test-summary-progress"

    clear_session_memory(session_id)

    max_turns = 2

    mock_summarize_memory = Mock(
        side_effect=[
            "第一次摘要",
            "第二次摘要"
        ]
    )

    monkeypatch.setattr(
        "app.memory_manager.summarize_memory",
        mock_summarize_memory
    )

    # -------------------------
    # 先制造 3 轮对话
    # -------------------------
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

    # 第一次更新 Summary
    update_summary_if_needed(
        session_id=session_id,
        max_turns=max_turns
    )
    assert get_summary(session_id) == "第一次摘要"

    # -------------------------
    # 再增加第 4 轮
    # -------------------------
    add_message(
        session_id,
        "user",
        "第4轮问题"
    )

    add_message(
        session_id,
        "assistant",
        "第4轮回答"
    )

    # 第二次更新 Summary
    update_summary_if_needed(
        session_id=session_id,
        max_turns=max_turns
    )
    assert get_summary(session_id) == "第二次摘要"

    # summarize_memory 应该总共只调用两次
    assert mock_summarize_memory.call_count== 2

    first_call = mock_summarize_memory.call_args_list[0]
    second_call = mock_summarize_memory.call_args_list[1]

    # 第一次：
    # 旧 Summary 为空
    assert first_call.kwargs["old_summary"] == ""

    # 第一次只总结第1轮
    assert first_call.kwargs["messages"] == [
        {
            "role": "user",
            "content": "第1轮问题"
        },
        {
            "role": "assistant",
            "content": "第1轮回答"
        }
    ]

    # 第二次：
    # 应该基于第一次摘要继续更新
    assert second_call.kwargs["old_summary"] == "第一次摘要"

    # 第二次只能总结新滑出去的第2轮
    # 不能把第1轮再总结一次
    assert second_call.kwargs["messages"] == [
        {
            "role": "user",
            "content": "第2轮问题"
        },
        {
            "role": "assistant",
            "content": "第2轮回答"
        }
    ]

    clear_session_memory(session_id)
