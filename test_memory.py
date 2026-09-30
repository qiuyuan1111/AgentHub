from app.memory import *


session_id = "summary-window-test"

clear_session_memory(session_id)


def add_turn(user_text, assistant_text):

    add_message(
        session_id,
        "user",
        user_text
    )

    add_message(
        session_id,
        "assistant",
        assistant_text
    )


# 第1轮
add_turn(
    "第1轮：订单是1001",
    "记住了订单1001"
)

# 第2轮
add_turn(
    "第2轮：颜色是蓝色",
    "记住了蓝色"
)

# 第3轮
add_turn(
    "第3轮：城市是南京",
    "记住了南京"
)


print("===== 最近2轮 =====")

print(
    get_recent_history(
        session_id,
        max_turns=2
    )
)


print("\n===== 第一次需要总结 =====")

old_messages = get_messages_to_summarize(
    session_id,
    max_turns=2
)

print(old_messages)


# 假装已经成功总结
mark_messages_summarized(
    session_id,
    len(old_messages)
)


print("\n===== 再次检查 =====")

print(
    get_messages_to_summarize(
        session_id,
        max_turns=2
    )
)


# 第4轮
add_turn(
    "第4轮：商品编号P001",
    "记住了P001"
)


print("\n===== 第4轮之后需要总结 =====")

print(
    get_messages_to_summarize(
        session_id,
        max_turns=2
    )
)