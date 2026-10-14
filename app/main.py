from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel,Field,field_validator


from app.memory import get_recent_history, add_message, get_summary, get_history, clear_session_memory
from app.llm import chat_with_tools
from app.memory_manager import update_summary_if_needed
from app.config import MAX_HISTORY_TURNS
from app.schemas import ApiResponse
from app.exceptions import AppException
from app.logger import get_logger
from fastapi.exceptions import RequestValidationError

import time
import uuid

logger = get_logger(__name__)

from app.request_context import (
    set_request_id,
    reset_request_id
)

# 创建一个 Web 后端应用
app = FastAPI()

@app.middleware("http")
async def request_context_middleware(
    request: Request,
    call_next
):
    request_id = str(uuid.uuid4())

    # FastAPI request对象中保存一份
    request.state.request_id = request_id

    # ContextVar中保存一份
    token = set_request_id(
        request_id
    )

    try:
        start_time = time.perf_counter()

        response = await call_next(request)

        elapsed = time.perf_counter() - start_time

        response.headers["X-Request-Id"] = request_id

        logger.info(
            "HTTP 请求完成 | "
            "method=%s | path=%s | "
            "status=%s | time=%.3fs",
            request.method,
            request.url.path,
            response.status_code,
            elapsed
        )

        return response
    finally:
        reset_request_id(token)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    request_id = getattr(
        request.state,
        "request_id",
        "-"
    )

    logger.error(
        "未处理异常 | request_id=%s | "
        "method=%s | path=%s",
        request_id,
        request.method,
        request.url.path,
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__
        )
    )

    response = ApiResponse(
        code=1001,
        message="服务器内部错误",
        data=None
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    errors = []

    for error in exc.errors():

        field = ".".join(
            str(item)
            for item in error["loc"]
            if item != "body"
        )

        errors.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            }
        )

        logger.warning(
            "请求参数校验失败 | errors=%s",
            errors
        )

        response = ApiResponse(
            code=2001,
            message="请求参数校验失败",
            data={
                "errors": errors
            }
        )

        return JSONResponse(
            status_code=422,
            content=response.model_dump()
        )

@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException
):
    request_id = getattr(
        request.state,
        "request_id",
        "-"
    )

    logger.error(
        "应用异常 | request_id=%s | "
        "method=%s | path=%s | "
        "code=%s | status=%s | message=%s",
        request_id,
        request.method,
        request.url.path,
        exc.code,
        exc.status_code,
        exc.message,
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__
        )
    )

    response = ApiResponse(
        code=exc.code,
        message=exc.message,
        data=None
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump()
    )

# 限定chatRequest里面一定要有 message
class chatRequest(BaseModel):

    session_id: str = Field(
        min_length=1,
        max_length=128
    )

    message: str = Field(
        min_length=1,
        max_length=2000
    )

    @field_validator(
        "session_id",
        "message",
        mode="before"
    )

    @classmethod
    def strip_text_fields(
        cls,
        value
    ):
        if isinstance(value, str):
            return value.strip()

        return value

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

    logger.debug(
        "当前 Summary | session_id=%s | summary=%s",
        request.session_id,
        summary
    )

    logger.debug(
        "当前 Recent History | session_id=%s | history=%s",
        request.session_id,
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

        logger.info(
            "Summary 更新成功 | session_id=%s",
            request.session_id
        )

    except Exception:
        logger.warning(
            "Summary 更新失败 | session_id=%s",
            request.session_id,
            exc_info=True
        )

    return ApiResponse(
        code=0,
        message="success",
        data={
            "session_id": request.session_id,
            "answer": answer
        }
    )

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

@app.get("/health")
def health():
    return ApiResponse(
        code=0,
        message="success",
        data={
        "status": "ok"
        }
    )



