from fastapi.testclient import TestClient

from app.main import app
from app.memory import clear_session_memory

from app.config import MAX_HISTORY_TURNS

client = TestClient(app)

def test_chat_success(monkeypatch):

    session_id = "test-chat-success"

    clear_session_memory(session_id)

    captured = {}

    def fake_chat_with_tools(
            message,
            history,
            summary=""
    ):
        captured["message"] = message
        captured["history"] = history
        captured["summary"] = summary

        return "这是一个模拟回答"

    summary_captured = {}

    def fake_update_summary_if_needed(
        session_id,
        max_turns
    ):
        summary_captured["session_id"] = session_id

        summary_captured["max_turns"] = max_turns

        return None

    monkeypatch.setattr(
        "app.main.chat_with_tools",
        fake_chat_with_tools
    )

    monkeypatch.setattr(
        "app.main.update_summary_if_needed",
        fake_update_summary_if_needed
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
    assert captured["message"] == "你好"

    assert captured["history"] == []

    assert captured["summary"] == ""

    assert summary_captured["session_id"] == session_id

    assert summary_captured["max_turns"] == MAX_HISTORY_TURNS

    clear_session_memory(session_id)