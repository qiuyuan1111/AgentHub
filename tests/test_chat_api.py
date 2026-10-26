from fastapi.testclient import TestClient

from app.main import app
from app.memory import clear_session_memory
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
