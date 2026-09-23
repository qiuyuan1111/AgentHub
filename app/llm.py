import os

from dotenv import load_dotenv
from openai import OpenAI

# 读取 .env 文件
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("没有读取到 DEEPSEEK_API_KEY, 请检查 .env 文件")

# 创建大模型客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

def chat(message:str):
    # 向大模型发送请求
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {
                "role":"system",
                "content":"你是 AgentHub 中的 AI 助手。"
            },
            {
                "role":"user",
                "content":message
            }
        ]
    )
    # 输出模型回答
    return response.choices[0].message.content