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