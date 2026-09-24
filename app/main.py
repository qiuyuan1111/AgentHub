from fastapi import FastAPI
from pydantic import BaseModel

from app.llm import chat_with_tools

# 创建一个 Web 后端应用
app = FastAPI()

# 限定chatRequest里面一定要有 message
class chatRequest(BaseModel):
    message: str

# 网页get"/"时触发
@app.get("/")
def root():
    return {
        "message": "AgentHub is running!"
    }

# 网页post"/chat"时触发
@app.post("/chat")
def chat_api(request: chatRequest):
    answer = chat_with_tools(request.message)
    return {
        "answer": answer
    }