from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["code"] == 0
    assert body["message"] == "success"
    assert body["data"]["status"] == "ok"

def test_chat_missing_message():
    response = client.post(
        "/chat",
        json={
            "session_id": "tests-session"
        }
    )

    assert response.status_code == 422

    body = response.json()

    assert body["code"] == 2001
    assert body["message"] == "请求参数校验失败"

    errors = body["data"]["errors"]

    assert errors[0]["field"] == "message"
    assert errors[0]["type"] == "missing"

def test_chat_empty_message():

    response = client.post(
        "/chat",
        json={
            "session_id": "tests-session",
            "message": ""
        }
    )

    assert response.status_code == 422

    body = response.json()

    assert body["code"] == 2001

    errors = body["data"]["errors"]

    assert errors[0]["field"] == "message"
    assert errors[0]["type"] == "string_too_short"

def test_chat_blank_message():

    response = client.post(
        "/chat",
        json={
            "session_id": "tests-session",
            "message": "     "
        }
    )

    assert response.status_code == 422

    body = response.json()

    errors = body["data"]["errors"]

    assert errors[0]["field"] == "message"
    assert errors[0]["type"] == "string_too_short"

def test_chat_blank_session_id():

    response = client.post(
        "/chat",
        json={
            "session_id": "     ",
            "message": "你好"
        }
    )

    assert response.status_code == 422

    body = response.json()

    errors = body["data"]["errors"]

    assert errors[0]["field"] == "session_id"
    assert errors[0]["type"] == "string_too_short"