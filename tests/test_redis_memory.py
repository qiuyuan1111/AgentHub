import json

from unittest.mock import Mock

from app.redis_memory import RedisMemoryStore

def test_redis_add_and_get_history():

    mock_client = Mock()

    # 当 `mock_client.lrange` 被调用时，返回这两条 json 字符串
    mock_client.lrange.return_value = [
        json.dumps(
            {
                "role": "user",
                "content": "你好"
            },
            ensure_ascii=False
        ),
        json.dumps(
            {
                "role": "assistant",
                "content": "你好"
            },
            ensure_ascii=False
        )
    ]

    store = RedisMemoryStore(
        client=mock_client
    )

    store.add_message(
        "session-1",
        "user",
        "你好"
    )

    # 检查是否真的调用 RPUSH
    rpush_call = mock_client.rpush.call_args

    assert rpush_call.args[0] == "agenthub:memory:session-1:messages"

    saved_message = json.loads(rpush_call.args[1])
    assert saved_message == {
        "role": "user",
        "content": "你好"
    }

    history = store.get_history("session-1")
    mock_client.lrange.assert_called_once_with(
        "agenthub:memory:session-1:messages",
        0,
        -1
    )

    assert history == [
        {
            "role": "user",
            "content": "你好"
        },
        {
            "role": "assistant",
            "content": "你好"
        }
    ]

def test_redis_get_recent_history():

    mock_client = Mock()

    mock_client.lrange.return_value = [
        json.dumps(
            {
                "role": "user",
                "content": "第3轮问题"
            },
            ensure_ascii=False
        ),
        json.dumps(
            {
                "role": "assistant",
                "content": "第3轮回答"
            },
            ensure_ascii=False
        )
    ]

    store = RedisMemoryStore(
        client=mock_client
    )

    history = store.get_recent_history(
        session_id="session-1",
        max_turns=1
    )

    mock_client.lrange.assert_called_once_with(
        "agenthub:memory:session-1:messages",
        -2,
        -1
    )

    assert history == [
        {
            "role": "user",
            "content": "第3轮问题"
        },
        {
            "role": "assistant",
            "content": "第3轮回答"
        }
    ]

def test_redis_clear_session_memory():

    mock_client = Mock()

    store = RedisMemoryStore(
        client=mock_client
    )

    store.clear_session_memory(
        "session-1"
    )

    mock_client.delete.assert_called_once_with(
        "agenthub:memory:session-1:messages",
        "agenthub:memory:session-1:summary",
        "agenthub:memory:session-1:summary_progress"
    )