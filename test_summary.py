from app.llm import summarize_memory

old_summary = "用户当前关注订单1001。"

messages = [
    {
        "role": "user",
        "content": "刚才说错了，我其实想查的是订单1002。"
    },
    {
        "role": "assistant",
        "content": "好的。"
    }
]


new_summary = summarize_memory(
    old_summary=old_summary,
    messages=messages
)


print("===== 旧摘要 =====")
print(old_summary)

print("\n===== 新摘要 =====")
print(new_summary)