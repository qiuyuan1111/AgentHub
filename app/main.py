from fastapi import FastAPI
from pydantic import BaseModel
from app.memory import get_recent_history, add_message, get_summary, get_history, clear_session_memory
from app.llm import chat_with_tools
from app.memory_manager import update_summary_if_needed


MAX_HISTORY_TURNS = 5

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

    # 1. 获取较早历史的摘要
    summary = get_summary(
        request.session_id
    )

    # 2. 获取最近 N 轮完整历史
    history = get_recent_history(
        session_id=request.session_id,
        max_turns=MAX_HISTORY_TURNS
    )

    print(
        "当前 Summary:",
        summary
    )

    print(
        "当前发送给 LLM 的历史:",
        history
    )

    # 3. Summary + 最近历史 + 当前问题
    answer = chat_with_tools(
        message=request.message,
        history=history,
        summary=summary
    )

    # 4. 保存本轮用户消息
    add_message(
        session_id=request.session_id,
        role="user",
        content=request.message
    )

    # 5. 保存本轮最终回答
    add_message(
        session_id=request.session_id,
        role="assistant",
        content=answer
    )

    try:
        # 6. 当前轮结束后，检查有没有消息刚刚滑出窗口
        new_summary = update_summary_if_needed(
            session_id=request.session_id,
            max_turns=MAX_HISTORY_TURNS
        )

        if new_summary:
            print(
                "Summary 已更新:",
                new_summary
            )

    except Exception as e:
        print("Summary 更新失败:", e)

    return {
        "session_id": request.session_id,
        "answer": answer
    }

@app.get("/memory/{session_id}")
def get_memory(session_id: str):

    return {
        "session_id": session_id,
        "summary": get_summary(session_id),
        "recent_history": get_recent_history(session_id=session_id, max_turns=MAX_HISTORY_TURNS),
        "full_history": get_history(session_id=session_id)
    }

@app.delete("/memory/{session_id}")
def clear_memory(session_id: str):

    clear_session_memory(session_id)
    return {
        "session_id": session_id,
        "message": "会话记忆已清空"
    }