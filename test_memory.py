from app.memory import *

session_id = "test_session"

print("===== 初始 =====")

print(
    get_history(session_id)
)

add_message(
    session_id,
    "user",
    "订单1001到哪了？"
)

add_message(
    session_id,
    "assistant",
    "订单1001正在配送。"
)

print("\n===== 添加消息后 =====")

print(
    get_history(session_id)
)

clear_history(session_id)

print("\n===== 清空后 =====")

print(
    get_history(session_id)
)