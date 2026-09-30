from app.memory import (
    get_summary,
    get_messages_to_summarize,
    set_summary,
    mark_messages_summarized
)

from app.llm import summarize_memory

def update_summary_if_needed(
    session_id: str,
    max_turns: int
) -> str | None:


    messages_to_summarize = get_messages_to_summarize(
        session_id=session_id,
        max_turns=max_turns
    )

    # 没有新的旧消息需要总结
    if not messages_to_summarize:
        return None

    old_summary = get_summary(session_id=session_id)

    # 调用 LLM 生成新摘要
    new_summary = summarize_memory(
        old_summary=old_summary,
        messages=messages_to_summarize
    )

    # 摘要成功生成后再保存
    set_summary(
        session_id=session_id,
        summary=new_summary
    )

    # 最后再标记这些消息已经总结过
    mark_messages_summarized(
        session_id=session_id,
        message_count=len(messages_to_summarize)
    )

    return new_summary