import json

from redis import Redis
from app.config import REDIS_URL

from app.memory import MemoryStore

class RedisMemoryStore(MemoryStore):

    def __init__(
        self,
        client: Redis | None = None
    ):
        # 测试时可以传 Mock client
        # 正式运行时才真正连接 Redis
        self.client = (
            client
            or Redis.from_url( #自动根据 `REDIS_URL` 创建 Redis 实例
                REDIS_URL,
                decode_responses=True # Redis 返回的值自动转字符串
            )
        )

    def _messages_key(self, session_id: str) -> str:
        return f"agenthub:memory:{session_id}:messages"

    def _summary_key(self, session_id: str) -> str:
        return f"agenthub:memory:{session_id}:summary"

    def _summary_progress_key(self, session_id: str) -> str:
        return f"agenthub:memory:{session_id}:summary_progress"

    def add_message(
            self,
            session_id: str,
            role: str,
            content: str
    ) -> None:
        message = {
            "role": role,
            "content": content
        }

        self.client.rpush(
            self._messages_key(session_id),
            json.dumps(
                message,
                ensure_ascii=False # 如果是中文不会采用 ASCII 码
            )
        )

    def get_history(
        self,
        session_id: str
    ) -> list[dict]:
        # 取出 List 全部元素
        raw_messages = self.client.lrange(self._messages_key(session_id), 0, -1)
        # 把每一条 json 字符串反序列化成字典，返回完整对话历史
        return [json.loads(message) for message in raw_messages]

    def get_recent_history(
        self,
        session_id: str,
        max_turns: int
    ) -> list[dict]:

        max_messages = max_turns * 2

        if max_messages <= 0:
            return []

        # `lrange key -N -1`：取 List 最后 N 条
        # 消息不足 N 条时 Redis 原生兼容，直接返回现有全部消息
        raw_messages = self.client.lrange(self._messages_key(session_id), -max_messages, -1)
        return [json.loads(message) for message in raw_messages]

    # 只占位，没有写逻辑，调用就抛异常
    def get_summary(
        self,
        session_id: str
    ) -> str:
        raise NotImplementedError

    def set_summary(
        self,
        session_id: str,
        summary: str
    ) -> None:
        raise NotImplementedError

    def get_messages_to_summarize(
        self,
        session_id: str,
        max_turns: int
    ) -> list[dict]:
        raise NotImplementedError

    def mark_messages_summarized(
        self,
        session_id: str,
        message_count: int
    ) -> None:
        raise NotImplementedError

    def clear_session_memory(self, session_id: str) -> None:
        self.client.delete(
            self._messages_key(session_id),
            self._summary_key(session_id),
            self._summary_progress_key(session_id)
        )


