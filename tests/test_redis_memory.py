import json

from unittest.mock import Mock

from app.redis_memory import RedisMemoryStore

# client 的 get/set 就是 redis 的原生命令

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

def test_redis_summary():

    mock_client = Mock()

    mock_client.get.return_value = "这是历史摘要"

    store = RedisMemoryStore(
        client=mock_client
    )

    store.set_summary(
        "session-1",
        "这是历史摘要"
    )

    mock_client.set.assert_called_once_with(
        "agenthub:memory:session-1:summary",
        "这是历史摘要"
    )

    summary = store.get_summary(
        "session-1"
    )

    mock_client.get.assert_called_once_with(
        "agenthub:memory:session-1:summary"
    )

    assert summary == "这是历史摘要"

def test_redis_summary_defaults_to_empty():

    mock_client = Mock()

    mock_client.get.return_value = None

    store = RedisMemoryStore(
        client=mock_client
    )

    assert store.get_summary("session-1") == ""

def test_redis_mark_messages_summarized():

    mock_client = Mock()

    store = RedisMemoryStore(
        client=mock_client
    )

    # 底层是 incrby
    store.mark_messages_summarized(
        session_id="session-1",
        message_count=2
    )

    # 断言：mock_client.incrby 被恰好调用1次
    # key = agenthub:memory:session-1:summary_progress，增量值=2
    mock_client.incrby.assert_called_once_with(
        "agenthub:memory:session-1:summary_progress",
        2
    )

def test_redis_get_messages_to_summarize():

    mock_client = Mock()

    # 消息列表总长度6条
    mock_client.llen.return_value = 6

    # summary_progress 计数器不存在，代表之前没有消息被总结过
    mock_client.get.return_value = None

    # mock lrange 返回的原始字符串消息列表
    mock_client.lrange.return_value = [
        json.dumps(
            {
                "role": "user",
                "content": "第1轮问题"
            },
            ensure_ascii=False
        ),
        json.dumps(
            {
                "role": "assistant",
                "content": "第1轮回答"
            },
            ensure_ascii=False
        )
    ]

    store = RedisMemoryStore(
        client=mock_client
    )

    messages = (
        store.get_messages_to_summarize(
            session_id="session-1",
            max_turns=2
        )
    )

    # 断言：调用llen统计消息队列长度，key：agenthub:memory:session-1:messages
    mock_client.llen.assert_called_once_with(
        "agenthub:memory:session-1:messages"
    )

    # 断言：lrange取下标0~1的数据（前2条）
    # 逻辑：总6条，保留最近max_turns*2=4条，剩下前面0~1取出用于摘要
    mock_client.lrange.assert_called_once_with(
        "agenthub:memory:session-1:messages",
        0,
        1
    )

    # 断言：内部自动json loads，返回解析后的消息字典数组
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

def test_redis_does_not_repeat_summarized_messages():

    mock_client = Mock()

    # 现在8条消息 = 4轮
    mock_client.llen.return_value = 8

    # 前2条以前已经总结过
    mock_client.get.return_value = "2"

    mock_client.lrange.return_value = [
        json.dumps(
            {
                "role": "user",
                "content": "第2轮问题"
            },
            ensure_ascii=False
        ),
        json.dumps(
            {
                "role": "assistant",
                "content": "第2轮回答"
            },
            ensure_ascii=False
        )
    ]

    store = RedisMemoryStore(
        client=mock_client
    )

    # 以上的所有 return_value 都是为了用在这个函数里面
    messages = (
        store.get_messages_to_summarize(
            session_id="session-1",
            max_turns=2
        )
    )

    # 8 - 4 = 4
    #
    # 需要总结的范围本来是：
    # [0, 4)
    #
    # 但0、1以前已经总结过
    #
    # 所以只读取：
    # 2、3
    mock_client.lrange.assert_called_once_with(
        "agenthub:memory:session-1:messages",
        2,
        3
    )

    assert messages == [
        {
            "role": "user",
            "content": "第2轮问题"
        },
        {
            "role": "assistant",
            "content": "第2轮回答"
        }
    ]
