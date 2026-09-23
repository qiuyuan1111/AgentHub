import os


from app.llm import chat

answer = chat("请用大白话解释什么是 RAG。")
print(answer)