conversation_store: dict[str, list[str]] = {}
MAX_HISTORY_TURNS = 5

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

def clear_history(session_id: str):
    conversation_store.pop(
        session_id,
        None  # 如果这个 session 根本不存在，也不要报错。
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