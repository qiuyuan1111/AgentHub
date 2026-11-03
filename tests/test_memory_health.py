import pytest

from redis.exceptions import (
    ConnectionError as RedisConnectionError
)

from unittest.mock import Mock

from app.memory import (
    InMemoryMemoryStore
)

from app.redis_memory import (
    RedisMemoryStore
)

def test_in_memory_store_is_healthy():

    store = InMemoryMemoryStore()

    assert store.health_check() is True

def test_redis_store_is_healthy():

    mock_client = Mock()

    mock_client.ping.return_value = True

    store = RedisMemoryStore(
        client=mock_client
    )

    assert store.health_check() is True

    mock_client.ping.assert_called_once_with()

# 确保RedisMemoryStore 不要偷偷吃掉这个异常
def test_redis_store_health_check_raises_when_unavailable():

    mock_client = Mock()

    mock_client.ping.side_effect = (
        RedisConnectionError(
            "Redis unavailable"
        )
    )

    store = RedisMemoryStore(
        client=mock_client
    )

    with pytest.raises(
        RedisConnectionError
    ):
        store.health_check()