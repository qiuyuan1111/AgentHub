import os


from app.llm import chat
from app.llm import chat_with_tools

# answer = chat("请用大白话解释什么是 RAG。")
# print(answer)

result = chat_with_tools("你好，你是谁？")
print("最终回答:\n", result)