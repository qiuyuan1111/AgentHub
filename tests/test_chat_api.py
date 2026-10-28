from fastapi.testclient import TestClient

from app.main import app
from app.memory import (
    clear_session_memory,
    set_summary,
)
from app.config import MAX_HISTORY_TURNS

from unittest.mock import Mock

client = TestClient(app)

def test_chat_success(monkeypatch):

    session_id = "test-chat-success"

    clear_session_memory(session_id)

    mock_chat_with_tools = Mock(
        return_value="这是一个模拟回答"
    )

    mock_update_summary = Mock(
        return_value=None
    )

    monkeypatch.setattr(
        "app.main.chat_with_tools",
        mock_chat_with_tools
    )

    monkeypatch.setattr(
        "app.main.update_summary_if_needed",
        mock_update_summary
    )

    response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "你好"
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert body["code"] == 0
    assert body["message"] == "success"

    assert body["data"]["session_id"] == session_id

    assert body["data"]["answer"] == \
        "这是一个模拟回答"

    assert "X-Request-ID" in response.headers

    # 检查 /chat 真正传给 Agent 的参数
    mock_chat_with_tools.assert_called_once_with(
        message="你好",
        history=[],
        summary=""
    )

    mock_update_summary.assert_called_once_with(
        session_id=session_id,
        max_turns=MAX_HISTORY_TURNS
    )
    clear_session_memory(session_id)

def test_chat_second_turn_receives_history(
    monkeypatch
):
    session_id = "test-chat-memory"

    clear_session_memory(
        session_id
    )

    mock_chat_with_tools = Mock(
        side_effect=[
            "第一轮模拟回答",
            "第二轮模拟回答"
        ]
    )

    mock_update_summary = Mock(
        return_value=None
    )

    monkeypatch.setattr(
        "app.main.chat_with_tools",
        mock_chat_with_tools
    )

    monkeypatch.setattr(
        "app.main.update_summary_if_needed",
        mock_update_summary
    )

    # 第一轮
    response1 = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "第一轮问题"
        }
    )

    assert response1.status_code == 200

    # 第二轮
    response2 = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "第二轮问题"
        }
    )

    assert response2.status_code == 200

    # 确认 Agent 一共被调用两次
    assert mock_chat_with_tools.call_count == 2

    first_call = mock_chat_with_tools.call_args_list[0]

    second_call = mock_chat_with_tools.call_args_list[1]

    # 第一轮
    assert first_call.kwargs["message"]== "第一轮问题"

    assert first_call.kwargs["history"]== []

    assert first_call.kwargs["summary"] == ""

    # 第二轮
    assert second_call.kwargs["message"]== "第二轮问题"


    assert second_call.kwargs["history"] == [
        {
            "role": "user",
            "content": "第一轮问题"
        },
        {
            "role": "assistant",
            "content": "第一轮模拟回答"
        }
    ]

    assert (
        second_call.kwargs["summary"]
        == ""
    )

    clear_session_memory(
        session_id
    )

def test_chat_sessions_are_isolated(monkeypatch):

    session_a = "test-session-a"
    session_b = "test-session-b"

    clear_session_memory(session_a)
    clear_session_memory(session_b)

    mock_chat_with_tools = Mock(
        side_effect=[
            "A的模拟回答",
            "B的模拟回答"
        ]
    )

    mock_update_summary = Mock(
        return_value=None
    )

    monkeypatch.setattr(
        "app.main.chat_with_tools",
        mock_chat_with_tools
    )

    monkeypatch.setattr(
        "app.main.update_summary_if_needed",
        mock_update_summary
    )

    # Session A 第一轮
    response_a = client.post(
        "/chat",
        json={
            "session_id": session_a,
            "message": "我是A"
        }
    )
    assert response_a.status_code == 200

    # Session B 第一轮
    response_b = client.post(
        "/chat",
        json={
            "session_id": session_b,
            "message": "我是B"
        }
    )
    assert response_b.status_code == 200
    assert mock_chat_with_tools.call_count == 2

    first_call = mock_chat_with_tools .call_args_list[0]

    second_call = mock_chat_with_tools.call_args_list[1]

    # A第一次请求，没有历史
    assert first_call.kwargs["message"] == "我是A"

    assert  first_call.kwargs["history"] == []

    # B也是第一次请求
    # 不能拿到A的历史
    assert second_call.kwargs["message"] == "我是B"

    assert second_call.kwargs["history"]== []

    clear_session_memory(session_a)
    clear_session_memory(session_b)

def test_chat_recent_history_window(monkeypatch):

    session_id = "test-history-window"

    clear_session_memory(session_id)

    # total_turns 要超过 MAX_HISTORY_TURNS 以验证是否正确截断
    total_turns = MAX_HISTORY_TURNS + 2

    mock_chat_with_tools = Mock(
        side_effect=[
            f"第{i}轮模拟回答"
            for i in range(1, total_turns + 1)
        ]
    )

    mock_update_summary = Mock(
        return_value=None
    )

    monkeypatch.setattr(
        "app.main.chat_with_tools",
        mock_chat_with_tools
    )

    monkeypatch.setattr(
        "app.main.update_summary_if_needed",
        mock_update_summary
    )

    for i in range(1, total_turns + 1):

        response = client.post(
            "/chat",
            json={
                "session_id": session_id,
                "message": f"第{i}轮问题"
            }
        )
        assert response.status_code == 200



    # 看最后一次调用 Agent 时收到的 history
    last_call = mock_chat_with_tools.call_args_list[-1]

    assert last_call.kwargs["message"]== f"第{total_turns}轮问题"

    history = last_call.kwargs["history"]

    # Recent History 最多只能有：
    # MAX_HISTORY_TURNS * 2 条消息
    assert len(history) == MAX_HISTORY_TURNS * 2

    first_history_turn = total_turns - MAX_HISTORY_TURNS

    assert history[0] == {
        "role": "user",
        "content": f"第{first_history_turn}轮问题"
    }

    assert history[1] == {
        "role": "assistant",
        "content": f"第{first_history_turn}轮模拟回答"
    }

    # 为什么是第 total_turns - 1 轮？
    # 因为第 total_turns 轮进入 Agent 时，第 total_turns 轮当前问题还没有写进 history。
    assert history[-2] == {
        "role": "user",
        "content": f"第{total_turns - 1}轮问题"
    }

    assert history[-1] == {
        "role": "assistant",
        "content": f"第{total_turns - 1}轮模拟回答"
    }

    clear_session_memory(session_id)

# Memory 里已经存在的 Summary，/chat 调用 chat_with_tools() 时真的会把它传进去。
def test_chat_receives_existing_summary(monkeypatch):

    session_id = "test-chat-summary"

    clear_session_memory(session_id)

    # 模拟这个会话之前已经生成过长期摘要
    set_summary(
        session_id,
        "用户之前查询过订单1001"
    )

    mock_chat_with_tools = Mock(
        return_value="模拟回答"
    )

    mock_update_summary = Mock(
        return_value=None
    )

    monkeypatch.setattr(
        "app.main.chat_with_tools",
        mock_chat_with_tools
    )

    monkeypatch.setattr(
        "app.main.update_summary_if_needed",
        mock_update_summary
    )

    response = client.post(
        "/chat",
        json={
            "session_id": session_id,
            "message": "我之前查的是哪个订单？"
        }
    )

    assert response.status_code == 200

    mock_chat_with_tools.assert_called_once_with(
        message="我之前查的是哪个订单？",
        history=[],
        summary="用户之前查询过订单1001"
    )

    clear_session_memory(
        session_id
    )
