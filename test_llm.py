import os
from platform import system
from xmlrpc import client

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.admin.organization import role

# 读取 .env 文件
load_dotenv()

# 从环境变量里获取 API Key
api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("没有读取到 DEEPSEEK_API_KEY, 请检查 .env 文件")

# 创建大模型客户端
client = OpenAI(
    api_key = api_key,
    base_url="https://api.deepseek.com"
)

# 向大模型发送请求
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {
            "role":"system",
            "content":"你是一个专业的ai助手。"
        },
        {
            "role":"user",
            "content":"请用大白话解释一下什么是 AI Agent。"
        }
    ]
)

# 输出模型回答
print(response.choices[0].message.content)