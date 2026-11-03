from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sympy import true

from app.main import app

def test_app_starts_when_memory_store_is_healthy(
    monkeypatch
):

    mock_health_check = Mock(
        return_value=true
    )

    monkeypatch.setattr(
        "app.main.check_memory_store_health",
        mock_health_check
    )

    with TestClient(app) as client: # 这里触发 mock_health_check

        response = client.get("/health") # 看 fastapi 是否启动成功
        assert response.status_code == 200

    mock_health_check.assert_called_once_with()

def test_app_fails_to_start_when_memory_store_is_unavailable(
    monkeypatch
):

    mock_health_check = Mock(
        side_effect=RuntimeError(
            "Redis unavailable"
        )
    )

    monkeypatch.setattr(
        "app.main.check_memory_store_health",
        mock_health_check
    )

    # 监控异常：期望进入 TestClient 时抛出 RuntimeError，message 匹配
    with pytest.raises(
        RuntimeError,
        match="Redis unavailable"
    ):
        # 进入 TestClient 上下文，触发 lifespan startup
        with TestClient(app):
            pass