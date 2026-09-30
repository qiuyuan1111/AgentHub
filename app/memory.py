conversation_store: dict[str, list[str]] = {}
MAX_HISTORY_TURNS = 5
summary_store: dict[str,str] = {}
# 这个 session 前多少条 message 已经被总结过。
summary_progress_store: dict[str,int] = {}

def get_messages_to_summarize(
    session_id: str,
    max_turns: int = MAX_HISTORY_TURNS
) -> list[dict]:

    history = conversation_store.get(
        session_id,
        []
    )

    max_recent_messaged = max_turns * 2

    # 最近 N 轮之前的消息数量
    cutoff = max(0, len(history) - max_recent_messaged)

    # 之前已经总结到哪里
    summarized_count = summary_progress_store.get(
        session_id,
        0
    )

    # 只返回：
    # 已经滑出窗口
    # 并且以前还没总结过
    return history[summarized_count:cutoff].copy()

def mark_messages_summarized(
    session_id: str,
    message_count: int
):
    current_count = summary_progress_store.get(
        session_id,
        0
    )

    summary_progress_store[session_id] = current_count + message_count

def get_summary(session_id: str) -> str:
    return summary_store.get(
        session_id,
        ""
    )

def set_summary(
    session_id: str,
    summary: str
):
    summary_store[session_id] = summary

def get_history(session_id: str) -> list[dict]:
    return conversation_store.get(
        session_id,
        []
    ).copy()

def add_message(
        session_id: str,
        role: str,
        content: str,
):
    if session_id not in conversation_store:
        conversation_store[session_id] = []
    conversation_store[session_id].append(
        {
            "role": role,
            "content": content
        }
    )

def clear_session_memory(session_id: str):
    conversation_store.pop(
        session_id,
        None  # 如果这个 session 根本不存在，也不要报错。
    )

    summary_store.pop(
        session_id,
        None
    )

    summary_progress_store.pop(
        session_id,
        None
    )

def get_recent_history(
    session_id: str,
    max_turns: int = MAX_HISTORY_TURNS
) -> list[dict]:

    history = conversation_store.get(
        session_id,
        []
    )

    max_messages = max_turns * 2

    return history[-max_messages:].copy()