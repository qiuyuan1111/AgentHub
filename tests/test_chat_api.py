from fastapi.testclient import TestClient

from app.main import app
from app.memory import clear_session_memory


client = TestClient(app)

def test_chat_success(monkeypatch):

    session_id = "test-chat-success"

    clear_session_memory(session_id)

    def fake_chat_with_tools(
            message,
            history,
            summary=""
    ):
        return "这是一个模拟回答"

    def fake_update_summary_if_needed(
        session_id,
        max_turns
    ):
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

    clear_session_memory(session_id)