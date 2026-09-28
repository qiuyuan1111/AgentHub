from fastapi import FastAPI
from pydantic import BaseModel
from app.memory import get_recent_history, add_message
from app.llm import chat_with_tools


# 创建一个 Web 后端应用
app = FastAPI()

# 限定chatRequest里面一定要有 message
class chatRequest(BaseModel):
    session_id: str
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

    # 1. 根据 session_id 获取之前的聊天记录
    history = get_recent_history(
        session_id=request.session_id,
        max_turns=5
    )

    # print(
    #     "当前发送给 LLM 的历史:",
    #     history
    # )

    # 2. 把历史 + 当前消息交给 Agent
    answer = chat_with_tools(
        message=request.message,
        history=history
    )

    add_message(
        session_id=request.session_id,
        role="user",
        content=request.message
    )

    add_message(
        session_id=request.session_id,
        role="assistant",
        content=answer
    )


    return {
        "session_id": request.session_id,
        "answer": answer
    }